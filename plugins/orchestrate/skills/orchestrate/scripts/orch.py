#!/usr/bin/env python3
"""Orchestrate driver for Claude Code.

Planners write plan.json; this script turns it into git worktrees, spawns
`claude -p` workers (or prepares prompts for Agent-tool subagents), records
handoffs, and keeps state.json reconciled from disk and git.

Stdlib only. Run `python3 orch.py --help` for subcommands.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = SKILL_DIR / "prompts"
ORCH = f"python3 {Path(__file__).resolve()}"

NAME_RE = re.compile(r"^[a-z0-9-]+$")
TASK_TYPES = ("worker", "subplanner", "verifier")
TERMINAL = ("handed-off", "error", "cancelled", "pruned")
VERIFICATION_VALUES = (
    "live-ui-verified",
    "unit-test-verified",
    "type-check-only",
    "verifier-blocked",
    "verifier-failed",
    "not-verified",
)
DEFAULT_MODELS = {"worker": "sonnet", "verifier": "sonnet", "subplanner": "opus", "root": "opus"}
DEFAULT_ALLOWED_TOOLS = [
    "Bash", "Read", "Edit", "Write", "MultiEdit", "Glob", "Grep",
    "Agent", "TodoWrite", "WebFetch", "WebSearch",
]
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_TIMEOUT_MIN = 90
DEFAULT_MAX_PARALLEL = 4

EXIT_DONE = 0
EXIT_FAILURES = 1
EXIT_PROGRESS = 2
EXIT_WAIT_ELAPSED = 3
EXIT_STUCK = 4


class OrchError(Exception):
    pass


# --------------------------------------------------------------------------- io

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def write_json(path: Path, data) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(path)


def git(args: list[str], cwd: Path | str, check: bool = True) -> str:
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    if check and r.returncode != 0:
        raise OrchError(f"git {' '.join(args)} failed in {cwd}: {r.stderr.strip()}")
    return r.stdout.strip()


class Workspace:
    def __init__(self, path: str | Path):
        self.dir = Path(path).resolve()
        if not (self.dir / "plan.json").exists():
            raise OrchError(f"no plan.json in {self.dir}")
        self.plan = read_json(self.dir / "plan.json")
        self.state = read_json(self.dir / "state.json", {"tasks": {}})
        self.state.setdefault("tasks", {})
        self.repo = Path(git(["rev-parse", "--show-toplevel"], self.dir))
        for d in ("handoffs", "logs", "prompts", "worktrees"):
            (self.dir / d).mkdir(exist_ok=True)
        self._exclude_workspace()

    # -- persistence
    def save(self) -> None:
        self.state["updatedAt"] = now()
        write_json(self.dir / "state.json", self.state)

    def attention(self, msg: str) -> None:
        line = f"{now()} {msg}\n"
        with open(self.dir / "attention.log", "a") as f:
            f.write(line)
        sys.stderr.write(f"[attention] {msg}\n")

    def _exclude_workspace(self) -> None:
        common = Path(git(["rev-parse", "--git-common-dir"], self.repo))
        if not common.is_absolute():
            common = (self.repo / common).resolve()
        exclude = common / "info" / "exclude"
        exclude.parent.mkdir(parents=True, exist_ok=True)
        text = exclude.read_text() if exclude.exists() else ""
        if ".orchestrate/" not in text.splitlines():
            with open(exclude, "a") as f:
                f.write(("\n" if text and not text.endswith("\n") else "") + ".orchestrate/\n")

    # -- plan helpers
    @property
    def slug(self) -> str:
        return self.plan["rootSlug"]

    def tasks(self) -> list[dict]:
        return self.plan.get("tasks", [])

    def task(self, name: str) -> dict:
        for t in self.tasks():
            if t["name"] == name:
                return t
        raise OrchError(f"unknown task: {name}")

    def row(self, name: str) -> dict:
        rows = self.state["tasks"]
        if name not in rows:
            rows[name] = {"name": name, "status": "pending", "attempts": 0}
        return rows[name]

    def deps(self, t: dict) -> list[str]:
        deps = list(t.get("dependsOn", []))
        if t["type"] == "verifier" and t.get("verifies") not in deps:
            deps.insert(0, t["verifies"])
        return deps

    def planned_branch(self, name: str) -> str:
        return f"orch/{self.slug}/{name}"

    def branch_for(self, name: str) -> str:
        r = self.state["tasks"].get(name, {})
        return r.get("reportedBranch") or r.get("branch") or self.planned_branch(name)

    def base_branch(self) -> str:
        return self.plan.get("baseBranch") or git(["rev-parse", "--abbrev-ref", "HEAD"], self.repo)

    def starting_ref(self, t: dict) -> str:
        ref = t.get("startingRef")
        if ref:
            m = re.fullmatch(rf"orch/{re.escape(self.slug)}/([a-z0-9-]+)", ref)
            if m and m.group(1) in self.state["tasks"]:
                return self.branch_for(m.group(1))
            return ref
        if t["type"] == "verifier":
            return self.branch_for(t["verifies"])
        return self.base_branch()

    def model_for(self, t: dict) -> str:
        if t.get("model"):
            return t["model"]
        return {**DEFAULT_MODELS, **self.plan.get("defaultModels", {})}[t["type"]]

    def andon(self) -> dict | None:
        own = self.state.get("andon")
        if own and own.get("raised"):
            return own
        p = self.plan.get("andonStatePath")
        if p and Path(p).exists():
            try:
                a = read_json(Path(p), {}).get("andon")
            except json.JSONDecodeError:
                return None
            if a and a.get("raised"):
                return a
        return None

    def handoff_path(self, name: str) -> Path:
        return self.dir / "handoffs" / f"{name}.md"

    def read_handoff(self, name: str) -> str | None:
        p = self.handoff_path(name)
        return p.read_text() if p.exists() else None


# ------------------------------------------------------------------- validation

def validate_plan(ws: Workspace) -> list[str]:
    errs: list[str] = []
    plan = ws.plan
    for key in ("goal", "rootSlug"):
        if not plan.get(key):
            errs.append(f"plan.{key} is required")
    if plan.get("rootSlug") and not NAME_RE.match(plan["rootSlug"]):
        errs.append("plan.rootSlug must be kebab-case ASCII")
    names = [t.get("name") for t in ws.tasks()]
    seen = set()
    for t in ws.tasks():
        n = t.get("name", "")
        if not NAME_RE.match(n or ""):
            errs.append(f"task name {n!r} must match {NAME_RE.pattern}")
        if n in seen:
            errs.append(f"duplicate task name {n}")
        seen.add(n)
        if t.get("type") not in TASK_TYPES:
            errs.append(f"{n}: type must be one of {TASK_TYPES}")
        if not t.get("scopedGoal"):
            errs.append(f"{n}: scopedGoal is required")
        if t.get("type") == "verifier":
            if t.get("verifies") not in names:
                errs.append(f"{n}: verifies must name a task in the plan")
            if t.get("openPR"):
                errs.append(f"{n}: verifiers never open PRs")
        elif "verifies" in t:
            errs.append(f"{n}: only verifiers take `verifies`")
        if t.get("type") == "subplanner" and t.get("openPR"):
            errs.append(f"{n}: subplanners never open PRs")
        for d in t.get("dependsOn", []):
            if d not in names:
                errs.append(f"{n}: dependsOn unknown task {d}")
        for m in t.get("measurements", []):
            if not m.get("name") or not m.get("command"):
                errs.append(f"{n}: measurements need name and command")
    # cycle check
    graph = {t["name"]: ws.deps(t) for t in ws.tasks() if t.get("name") and t.get("type")}
    state: dict[str, int] = {}

    def visit(n: str, stack: list[str]) -> None:
        if state.get(n) == 2 or n not in graph:
            return
        if state.get(n) == 1:
            errs.append(f"dependency cycle: {' -> '.join(stack + [n])}")
            return
        state[n] = 1
        for d in graph[n]:
            visit(d, stack + [n])
        state[n] = 2

    for n in graph:
        visit(n, [])
    return errs


def require_valid(ws: Workspace) -> None:
    errs = validate_plan(ws)
    if errs:
        raise OrchError("plan.json invalid:\n  " + "\n  ".join(errs))


# ---------------------------------------------------------------------- prompts

def render_template(name: str, vars: dict[str, str]) -> str:
    text = (PROMPTS_DIR / f"{name}.md").read_text()
    missing = sorted({k for k in re.findall(r"{{(\w+)}}", text) if k not in vars})
    if missing:
        raise OrchError(f"template {name} has unrendered placeholders: {', '.join(missing)}")
    # single pass so user text containing {{...}} is never re-expanded
    return re.sub(r"{{(\w+)}}", lambda m: vars[m.group(1)], text)


def _bullets(items, empty, box=False) -> str:
    items = items or []
    if not items:
        return f"  - {empty}"
    return "\n".join(f"  - [ ] {i}" if box else f"  - {i}" for i in items)


def _verify_block(t: dict | None, heading: str) -> str:
    if not t or not (t.get("verify") or "").strip():
        return ""
    return f"\n\n{heading}\n\n{t['verify']}\n"


def _upstream(ws: Workspace, t: dict) -> str:
    deps = ws.deps(t)
    if not deps:
        return ""
    chunks = []
    for d in deps:
        body = ws.read_handoff(d)
        if not body:
            chunks.append(f"### Upstream: `{d}`\n\n_(no handoff on disk; treat as missing context)_")
            continue
        body = re.sub(r"^<!--[\s\S]*?-->\s*", "", body).strip()
        chunks.append(f"### Upstream: `{d}` (branch `{ws.branch_for(d)}`)\n\n{body}")
    return (
        "\n\nUpstream handoffs (context from tasks you depend on; their branches exist in this "
        "repository, but this is the summary their authors wrote for you):\n\n"
        + "\n\n---\n\n".join(chunks)
        + "\n\n"
    )


def _scoped_goal(t: dict) -> str:
    brief = (t.get("brief") or "").strip()
    return f"Task brief:\n\n{brief}\n\n{t['scopedGoal']}" if brief else t["scopedGoal"]


def _handoff_instruction(handoff_file: Path | None) -> str:
    if handoff_file is None:
        return ""
    return (
        f"\n\nBefore you finish, also write your final message verbatim to `{handoff_file}` "
        "with the Write tool. The planner records that file; your returned text is a fallback."
    )


def render_prompt(ws: Workspace, name: str, worktree: Path, handoff_file: Path | None = None) -> str:
    t = ws.task(name)
    branch = ws.planned_branch(name)
    common = {
        "goal": ws.plan["goal"],
        "scopedGoal": _scoped_goal(t),
        "upstream": _upstream(ws, t),
        "worktree": str(worktree),
        "branch": branch,
        "startingRef": ws.starting_ref(t),
        "handoffInstruction": _handoff_instruction(handoff_file),
        "orch": ORCH,
    }
    if t["type"] == "worker":
        pr_base = ws.plan.get("prBase") or ws.base_branch()
        if t.get("openPR"):
            pr = (
                "- Keep `.orchestrate/` files out of the PR diff.\n"
                f"- After committing, push `{branch}` (`git push -u origin {branch}`) and open a draft "
                f"pull request with base `{pr_base}` (`gh pr create --draft --base {pr_base} --head {branch}`). "
                "Title and body summarize your handoff. Do NOT merge, rebase, or close the PR."
            )
        else:
            pr = "- Do NOT push, merge, rebase, or open a PR. The planner owns integration."
        merge = ""
        if t["name"].startswith("merge-"):
            sources = [ws.branch_for(d) for d in t.get("dependsOn", [])]
            merge = (
                "\n- This is a merge worker. Merge these branches into your branch one at a time, in order:\n"
                + "\n".join(f"  - {s}" for s in sources)
            )
        return render_template("worker", {
            **common,
            "allow": _bullets(t.get("pathsAllowed"), "(none declared; keep changes narrow)"),
            "forbid": _bullets(t.get("pathsForbidden"), "(none)"),
            "accept": _bullets(t.get("acceptance"), "(none declared)", box=True),
            "verifyPlan": _verify_block(t, "Verification plan (how the planner / a verifier will check your work):"),
            "mergeDiscipline": merge,
            "prDiscipline": pr,
        })
    if t["type"] == "verifier":
        target = next((x for x in ws.tasks() if x["name"] == t["verifies"]), None)
        return render_template("verifier", {
            **common,
            "targetName": t["verifies"],
            "targetType": target["type"] if target else "(unknown)",
            "targetBranch": ws.branch_for(t["verifies"]),
            "targetGoal": target["scopedGoal"] if target else "(target missing from plan)",
            "targetAccept": _bullets(target.get("acceptance") if target else None, "(none declared)"),
            "targetVerifyPlan": _verify_block(target, "Verification plan authored for the target (follow this as your recipe):"),
            "accept": _bullets(t.get("acceptance"), "(none declared)", box=True),
            "ownVerifyPlan": _verify_block(t, "Your own verification plan (planner-authored for this verifier task):"),
        })
    andon_path = ws.plan.get("andonStatePath") or str(ws.dir / "state.json")
    return render_template("subplanner", {
        **common,
        "name": name,
        "childSlug": f"{ws.slug}-{name}",
        "skillDir": str(SKILL_DIR),
        "andonStatePath": andon_path,
        "allow": _bullets(t.get("pathsAllowed"), "(none declared)"),
        "forbid": _bullets(t.get("pathsForbidden"), "(none)"),
        "accept": _bullets(t.get("acceptance"), "(none declared)", box=True),
        "verifyPlan": _verify_block(t, "Verification plan (how the planner / a verifier will check your work):"),
        "loopHygiene": render_template("loop-hygiene", {"orch": ORCH}),
    })


# --------------------------------------------------------------------- worktrees

def ensure_worktree(ws: Workspace, name: str, attempt: int) -> tuple[Path, str]:
    t = ws.task(name)
    branch = ws.planned_branch(name)
    path = ws.dir / "worktrees" / name
    start = ws.starting_ref(t)
    if path.exists():
        git(["worktree", "remove", "--force", str(path)], ws.repo, check=False)
        if path.exists():
            shutil.rmtree(path)
        git(["worktree", "prune"], ws.repo, check=False)
    exists = bool(git(["branch", "--list", branch], ws.repo))
    if exists and t["type"] != "subplanner":
        # Workers and verifiers start fresh; keep the old attempt for forensics.
        old = f"{branch}-attempt{attempt - 1}"
        git(["branch", "-f", old, branch], ws.repo)
        git(["branch", "-f", branch, start], ws.repo)
        ws.attention(f"{name}: previous attempt kept on {old}; restarting {branch} from {start}")
    elif not exists:
        git(["branch", branch, start], ws.repo)
    git(["worktree", "add", str(path), branch], ws.repo)
    return path, branch


# ----------------------------------------------------------------------- parsing

def section(body: str, heading: str) -> str | None:
    m = re.search(rf"^##\s+{re.escape(heading)}\s*$\n([\s\S]*?)(?=^##\s|\Z)", body, re.M)
    return m.group(1).strip() if m else None


def first_line(text: str | None) -> str:
    if not text:
        return ""
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def parse_handoff(body: str) -> dict:
    out: dict = {}
    status = first_line(section(body, "Status")).lower()
    for s in ("success", "partial", "blocked"):
        if status.startswith(s):
            out["handoffStatus"] = s
    branch = first_line(section(body, "Branch")).strip("` ")
    m = re.match(r"`?([^`\s]+)`?", branch)
    if m and not branch.startswith("("):
        out["branch"] = m.group(1)
    ver = first_line(section(body, "Verification")).strip("`< >").lower()
    for v in VERIFICATION_VALUES:
        if ver.startswith(v):
            out["verification"] = v
    if "verification" not in out:
        verdict = first_line(section(body, "Verdict")).lower()
        legacy = {"pass": "type-check-only", "fail": "verifier-failed", "inconclusive": "verifier-blocked"}
        for k, v in legacy.items():
            if verdict.startswith(k):
                out["verification"] = v
    return out


def has_structured_handoff(task_type: str, body: str) -> bool:
    key = "Verification" if task_type == "verifier" else "Status"
    return section(body, key) is not None


# ------------------------------------------------------------------ measurements

NUM_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*([A-Za-z%]*)")


def parse_measure_value(s: str):
    m = NUM_RE.search(s)
    if not m:
        return s.strip()
    return (float(m.group(1)), m.group(2))


def reported_measurement(body: str, name: str) -> str | None:
    """The worker's claimed final value for `name` (text after the last operator)."""
    sec = section(body, "Measurements") or ""
    for line in sec.splitlines():
        line = line.strip().lstrip("-").strip().strip("`")
        if line.startswith(name + ":"):
            rest = line[len(name) + 1:]
            return re.split(r"→|<=|>=|==|<|>", rest)[-1].strip().strip("`")
    return None


def check_measurements(ws: Workspace, t: dict, body: str, worktree: Path) -> None:
    ms = t.get("measurements") or []
    if not ms:
        return
    for m in ms:
        r = subprocess.run(["bash", "-c", m["command"]], cwd=str(worktree), capture_output=True, text=True)
        out = r.stdout
        parser = m.get("parser") or {"kind": "wc-l"}
        if parser["kind"] == "regex":
            flags = 0
            for ch in parser.get("flags", ""):
                flags |= {"i": re.I, "m": re.M, "s": re.S}.get(ch, 0)
            mm = re.search(parser["pattern"], out, flags)
            actual_s = (mm.group(1) if mm and mm.groups() else mm.group(0)) if mm else ""
        else:
            actual_s = str(len([ln for ln in out.splitlines() if ln.strip()]))
        claim = reported_measurement(body, m["name"])
        if claim is None:
            ws.attention(f"{t['name']}: measurement {m['name']!r} missing from handoff (actual {actual_s!r})")
            continue
        a, c = parse_measure_value(actual_s), parse_measure_value(claim)
        tol = m.get("toleranceFraction", 0.10)
        if isinstance(a, tuple) and isinstance(c, tuple):
            if a[1] and c[1] and a[1].lower() != c[1].lower():
                ws.attention(f"{t['name']}: measurement {m['name']!r} unit mismatch: claimed {claim!r}, actual {actual_s!r}")
            elif abs(a[0] - c[0]) > tol * max(abs(a[0]), 1e-9):
                ws.attention(f"{t['name']}: measurement {m['name']!r} drift >{tol:.0%}: claimed {claim!r}, actual {actual_s!r}")
        elif str(a) != str(c):
            ws.attention(f"{t['name']}: measurement {m['name']!r} mismatch: claimed {claim!r}, actual {actual_s!r}")


# ---------------------------------------------------------------------- handoffs

FAILURE_PATTERNS = [
    ("oom", re.compile(r"out of memory|OOMKilled|exit code 137", re.I)),
    ("network-drop", re.compile(r"fetch failed|ETIMEDOUT|ECONN|socket|dns|disconnect|overloaded|529|rate.?limit", re.I)),
    ("tool-error", re.compile(r"tool_use_failed|tool-error|tool error", re.I)),
]

SUGGESTIONS = {
    "cap-hit": "- Retry with smaller scope: split the task, tighten pathsAllowed, or lean out scopedGoal.\n- Or raise plan.taskTimeoutMinutes if the work was converging.",
    "oom": "- Retry with smaller scope.",
    "network-drop": "- Retry as-is; treat as transient (`respawn`).",
    "tool-error": "- Retry with a different `model`.",
    "unknown": "- Read the log and stderr. Retry as-is once, then abandon.",
}


def classify_failure(text: str, timed_out: bool, returncode: int | None) -> str:
    if timed_out:
        return "cap-hit"
    if returncode in (137, -9):
        return "oom"
    for mode, rx in FAILURE_PATTERNS:
        if rx.search(text or ""):
            return mode
    return "unknown"


def header(ws: Workspace, name: str, row: dict, extra: dict | None = None) -> str:
    fields = {
        "task": name,
        "type": ws.task(name)["type"],
        "branch": ws.branch_for(name),
        "attempt": row.get("attempts"),
        "backend": row.get("backend"),
        "sessionId": row.get("sessionId", ""),
        "recordedAt": now(),
        **(extra or {}),
    }
    lines = "\n".join(f"{k}: {v}" for k, v in fields.items())
    return f"<!-- orchestrate handoff\n{lines}\n-->\n\n"


def write_failure(ws: Workspace, name: str, row: dict, mode: str, error: str) -> None:
    started = row.get("startedAt", "")
    body = render_template("failure-handoff", {
        "taskName": name,
        "branch": ws.branch_for(name),
        "sessionId": row.get("sessionId") or "(unknown)",
        "failureMode": mode,
        "startedAt": started,
        "terminatedAt": now(),
        "log": row.get("log", "(none)"),
        "error": (error or "(none)").strip()[-2000:],
        "suggestions": SUGGESTIONS[mode],
    })
    (ws.dir / "handoffs" / f"{name}-failure.md").write_text(body)
    row.update(status="error", failureMode=mode, endedAt=now())
    ws.attention(f"{name}: error ({mode}); wrote handoffs/{name}-failure.md")


def record_body(ws: Workspace, name: str, body: str) -> str:
    """Persist a finished task's final message; returns the resulting status."""
    t = ws.task(name)
    row = ws.row(name)
    ws.handoff_path(name).write_text(header(ws, name, row) + body.rstrip() + "\n")
    row["endedAt"] = now()
    row["handoffPath"] = str(ws.handoff_path(name))
    if not has_structured_handoff(t["type"], body):
        snippet = body.strip()[:1500]
        side = render_template("finished-no-handoff", {
            "taskName": name,
            "branch": ws.branch_for(name),
            "sessionId": row.get("sessionId") or "(unknown)",
            "terminatedAt": now(),
            "rawSnippet": snippet or "(empty)",
        })
        (ws.dir / "handoffs" / f"{name}-finished-no-handoff.md").write_text(side)
        row.update(status="error", failureMode="finished-no-handoff")
        ws.attention(f"{name}: finished without a structured handoff")
        return "error"
    parsed = parse_handoff(body)
    if parsed.get("branch"):
        row["reportedBranch"] = parsed["branch"]
        if parsed["branch"] != row.get("branch"):
            ws.attention(f"{name}: handoff reports branch {parsed['branch']} (planned {row.get('branch')})")
    if parsed.get("handoffStatus"):
        row["handoffStatus"] = parsed["handoffStatus"]
    if parsed.get("verification"):
        target = t["verifies"] if t["type"] == "verifier" else name
        trow = ws.row(target)
        if t["type"] == "verifier" or not trow.get("verifiedBy"):
            trow["verification"] = parsed["verification"]
            trow["verifiedBy"] = name if t["type"] == "verifier" else None
    row["status"] = "handed-off"
    wt = row.get("worktree")
    if wt and Path(wt).exists() and t["type"] == "worker":
        try:
            check_measurements(ws, t, body, Path(wt))
        except Exception as e:  # measurement problems never block the handoff
            ws.attention(f"{name}: measurement check failed: {e}")
    return "handed-off"


# ---------------------------------------------------------------------- spawning

def pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    # Reap if it is our own zombie child.
    try:
        wpid, _ = os.waitpid(pid, os.WNOHANG)
        if wpid == pid:
            return False
    except ChildProcessError:
        pass
    try:
        stat = Path(f"/proc/{pid}/stat").read_text().split()
        if stat[2] == "Z":
            return False
    except OSError:
        pass
    return True


def claude_cmd(ws: Workspace, t: dict) -> list[str]:
    cmd = [os.environ.get("ORCH_CLAUDE_BIN", "claude"), "-p", "--output-format", "json", "--model", ws.model_for(t)]
    mode = ws.plan.get("permissionMode", "acceptEdits")
    cmd += ["--permission-mode", mode]
    tools = ws.plan.get("allowedTools", DEFAULT_ALLOWED_TOOLS)
    if tools:
        cmd += ["--allowedTools", ",".join(tools)]
    cmd += ws.plan.get("claudeArgs", [])
    return cmd


def spawn_cli(ws: Workspace, name: str) -> None:
    t = ws.task(name)
    row = ws.row(name)
    row["attempts"] = row.get("attempts", 0) + 1
    wt, branch = ensure_worktree(ws, name, row["attempts"])
    prompt = render_prompt(ws, name, wt)
    pfile = ws.dir / "prompts" / f"{name}.md"
    pfile.write_text(prompt)
    out = ws.dir / "logs" / f"{name}.attempt{row['attempts']}.json"
    err = ws.dir / "logs" / f"{name}.attempt{row['attempts']}.stderr"
    env = {**os.environ, "ORCH_WORKSPACE": str(ws.dir), "ORCH_TASK": name}
    with open(pfile) as fin, open(out, "w") as fout, open(err, "w") as ferr:
        p = subprocess.Popen(
            claude_cmd(ws, t), cwd=str(wt), stdin=fin, stdout=fout, stderr=ferr,
            env=env, start_new_session=True,
        )
    row.update(
        status="running", backend="cli", pid=p.pid, worktree=str(wt), branch=branch,
        startingRef=ws.starting_ref(t), model=ws.model_for(t), startedAt=now(),
        log=str(out), stderr=str(err), promptFile=str(pfile),
    )
    for k in ("endedAt", "failureMode", "sessionId", "reportedBranch", "handoffStatus"):
        row.pop(k, None)
    ws.save()
    print(json.dumps({"event": "spawned", "task": name, "branch": branch, "pid": p.pid, "model": row["model"]}))


def finish_cli(ws: Workspace, name: str, timed_out: bool = False) -> str:
    row = ws.row(name)
    raw = Path(row["log"]).read_text() if Path(row.get("log", "")).exists() else ""
    stderr = Path(row["stderr"]).read_text() if Path(row.get("stderr", "")).exists() else ""
    result = None
    try:
        result = json.loads(raw) if raw.strip() else None
    except json.JSONDecodeError:
        # stream may contain several JSON lines; take the last result object
        for line in reversed(raw.splitlines()):
            try:
                obj = json.loads(line)
                if obj.get("type") == "result":
                    result = obj
                    break
            except json.JSONDecodeError:
                continue
    if result:
        row["sessionId"] = result.get("session_id")
        row["costUsd"] = result.get("total_cost_usd")
        row["numTurns"] = result.get("num_turns")
    if timed_out:
        write_failure(ws, name, row, "cap-hit", stderr or "timed out")
        return "error"
    body = (result or {}).get("result") or ""
    if not result or (result.get("is_error") and not body.strip()):
        text = (json.dumps(result) if result else raw[-2000:]) + "\n" + stderr
        write_failure(ws, name, row, classify_failure(text, False, None), text)
        return "error"
    if result.get("subtype") and result["subtype"] != "success" and not has_structured_handoff(ws.task(name)["type"], body):
        write_failure(ws, name, row, classify_failure(stderr + body, False, None), f"subtype={result['subtype']}\n{body}")
        return "error"
    return record_body(ws, name, body)


# ---------------------------------------------------------------------- commands

def reconcile(ws: Workspace) -> None:
    names = {t["name"] for t in ws.tasks()}
    for name, row in ws.state["tasks"].items():
        if name not in names and row.get("status") not in TERMINAL:
            if row.get("status") == "running" and pid_alive(row.get("pid")):
                continue
            row["status"] = "pruned"
    for t in ws.tasks():
        r = ws.row(t["name"])
        r["type"] = t["type"]
        r.setdefault("branch", ws.planned_branch(t["name"]))


def ready_tasks(ws: Workspace) -> tuple[list[str], list[str]]:
    """Return (spawnable, blocked) pending task names."""
    ready, blocked = [], []
    for t in ws.tasks():
        row = ws.row(t["name"])
        if row["status"] != "pending":
            continue
        deps = ws.deps(t)
        if all(ws.row(d)["status"] == "handed-off" for d in deps):
            max_attempts = t.get("maxAttempts", DEFAULT_MAX_ATTEMPTS)
            if row.get("attempts", 0) >= max_attempts:
                row["status"] = "error"
                row["failureMode"] = "max-attempts"
                ws.attention(f"{t['name']}: exceeded maxAttempts={max_attempts}; bump it or abandon")
                continue
            ready.append(t["name"])
        elif any(ws.row(d)["status"] in ("error", "cancelled", "pruned") for d in deps):
            blocked.append(t["name"])
    return ready, blocked


def cmd_run(ws: Workspace, args) -> int:
    require_valid(ws)
    reconcile(ws)
    ws.save()
    max_parallel = args.max_parallel or ws.plan.get("maxParallel", DEFAULT_MAX_PARALLEL)
    timeout_s = 60 * ws.plan.get("taskTimeoutMinutes", DEFAULT_TIMEOUT_MIN)
    deadline = time.time() + args.max_wait
    new_handoffs: list[str] = []
    new_errors: list[str] = []
    andon_logged = False
    while True:
        running = [n for n, r in ws.state["tasks"].items() if r.get("status") == "running"]
        # reap finished / timed-out cli tasks
        for n in running:
            r = ws.row(n)
            if r.get("backend") != "cli":
                continue
            started = dt.datetime.fromisoformat(r["startedAt"]).timestamp()
            if pid_alive(r.get("pid")):
                if time.time() - started > timeout_s:
                    try:
                        os.killpg(r["pid"], signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    status = finish_cli(ws, n, timed_out=True)
                else:
                    continue
            else:
                status = finish_cli(ws, n)
            ws.save()
            (new_handoffs if status == "handed-off" else new_errors).append(n)
            print(json.dumps({"event": status, "task": n, "handoff": str(ws.handoff_path(n))}))
        running = [n for n, r in ws.state["tasks"].items() if r.get("status") == "running"]
        andon = ws.andon()
        ready, blocked = ([], []) if andon else ready_tasks(ws)
        if andon and not andon_logged:
            ws.attention(f"andon raised ({andon.get('reason')}); not spawning")
            andon_logged = True
        for n in ready[: max(0, max_parallel - len(running))]:
            if args.dry_run:
                print(json.dumps({"event": "would-spawn", "task": n}))
                continue
            try:
                spawn_cli(ws, n)
            except OrchError as e:
                r = ws.row(n)
                write_failure(ws, n, r, "unknown", f"spawn failed: {e}")
                new_errors.append(n)
            ws.save()
        if args.dry_run:
            return EXIT_DONE
        running = [n for n, r in ws.state["tasks"].items()
                   if r.get("status") == "running" and r.get("backend") == "cli"]
        if new_errors:
            return summarize(ws, EXIT_FAILURES, new_handoffs, new_errors)
        if new_handoffs and not args.until_done:
            return summarize(ws, EXIT_PROGRESS, new_handoffs, new_errors)
        if not running:
            pending = [n for n, r in ws.state["tasks"].items() if r.get("status") in ("pending", "running")]
            if not pending:
                return summarize(ws, EXIT_DONE, new_handoffs, new_errors)
            ready_now, _ = ([], []) if ws.andon() else ready_tasks(ws)
            if not ready_now:
                return summarize(ws, EXIT_STUCK, new_handoffs, new_errors)
            continue
        if time.time() > deadline:
            return summarize(ws, EXIT_WAIT_ELAPSED, new_handoffs, new_errors)
        time.sleep(args.poll)


def summarize(ws: Workspace, code: int, handed: list[str], errors: list[str]) -> int:
    ws.save()
    counts: dict[str, int] = {}
    for r in ws.state["tasks"].values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    meaning = {
        EXIT_DONE: "all tasks terminal",
        EXIT_FAILURES: "new failures: read the failure handoffs and decide",
        EXIT_PROGRESS: "new handoffs: read them, update plan.json if needed, rerun",
        EXIT_WAIT_ELAPSED: "max-wait elapsed with tasks still running: rerun",
        EXIT_STUCK: "pending tasks blocked (failed deps, andon, or agent-backend tasks still running)",
    }[code]
    print(json.dumps({"exit": code, "meaning": meaning, "newHandoffs": handed, "newErrors": errors, "counts": counts}))
    return code


def cmd_prepare(ws: Workspace, args) -> int:
    """Agent-tool backend: create the worktree and prompt, mark running."""
    require_valid(ws)
    reconcile(ws)
    t = ws.task(args.task)
    if t["type"] == "subplanner":
        raise OrchError("subplanners need their own Agent tool; run them with the cli backend (`run`)")
    row = ws.row(args.task)
    if row["status"] != "pending":
        raise OrchError(f"{args.task} is {row['status']}, not pending (use `respawn` first)")
    unmet = [d for d in ws.deps(t) if ws.row(d)["status"] != "handed-off"]
    if unmet:
        raise OrchError(f"{args.task} waits on: {', '.join(unmet)}")
    if ws.andon():
        raise OrchError("andon is raised; not spawning")
    row["attempts"] = row.get("attempts", 0) + 1
    wt, branch = ensure_worktree(ws, args.task, row["attempts"])
    hfile = ws.dir / "logs" / f"{args.task}.attempt{row['attempts']}.handoff.md"
    prompt = render_prompt(ws, args.task, wt, handoff_file=hfile)
    pfile = ws.dir / "prompts" / f"{args.task}.md"
    pfile.write_text(prompt)
    row.update(
        status="running", backend="agent", pid=None, worktree=str(wt), branch=branch,
        startingRef=ws.starting_ref(t), model=ws.model_for(t), startedAt=now(),
        promptFile=str(pfile), agentHandoffFile=str(hfile),
    )
    for k in ("endedAt", "failureMode", "sessionId", "reportedBranch", "handoffStatus"):
        row.pop(k, None)
    ws.save()
    agent = "orchestrate:orchestrate-verifier" if t["type"] == "verifier" else "orchestrate:orchestrate-worker"
    print(json.dumps({
        "task": args.task, "subagent_type": agent, "model": ws.model_for(t),
        "worktree": str(wt), "branch": branch, "promptFile": str(pfile), "handoffFile": str(hfile),
        "agentPrompt": f"Your task brief is at {pfile}. Read it in full and follow it exactly. "
                       f"Work only inside {wt}.",
    }, indent=2))
    return 0


def cmd_record(ws: Workspace, args) -> int:
    row = ws.row(args.task)
    body = None
    if args.file:
        body = sys.stdin.read() if args.file == "-" else Path(args.file).read_text()
    elif row.get("agentHandoffFile") and Path(row["agentHandoffFile"]).exists():
        body = Path(row["agentHandoffFile"]).read_text()
    if args.error:
        write_failure(ws, args.task, row, args.error, body or "subagent reported an error")
        ws.save()
        print(json.dumps({"task": args.task, "status": "error"}))
        return 0
    if body is None:
        raise OrchError("no handoff found: pass --file <path> (or - for stdin) with the subagent's final message")
    status = record_body(ws, args.task, body)
    ws.save()
    print(json.dumps({"task": args.task, "status": status, "handoff": str(ws.handoff_path(args.task))}))
    return 0


def cmd_prompt(ws: Workspace, args) -> int:
    t = ws.task(args.task)
    print(render_prompt(ws, t["name"], ws.dir / "worktrees" / t["name"]))
    return 0


def cmd_validate(ws: Workspace, args) -> int:
    errs = validate_plan(ws)
    if errs:
        print("\n".join(errs))
        return 1
    print("plan.json OK")
    return 0


def _status_rows(ws: Workspace):
    reconcile(ws)
    for t in ws.tasks():
        r = ws.row(t["name"])
        yield t, r


def cmd_status(ws: Workspace, args) -> int:
    rows = []
    for t, r in _status_rows(ws):
        alive = pid_alive(r.get("pid")) if r.get("status") == "running" and r.get("backend") == "cli" else None
        rows.append({
            "name": t["name"], "type": t["type"], "status": r["status"], "attempts": r.get("attempts", 0),
            "branch": ws.branch_for(t["name"]), "verification": r.get("verification"),
            "handoffStatus": r.get("handoffStatus"), "failureMode": r.get("failureMode"),
            "alive": alive, "deps": ws.deps(t),
        })
    if args.json:
        print(json.dumps({"andon": ws.andon(), "tasks": rows}, indent=2))
        return 0
    a = ws.andon()
    if a:
        print(f"ANDON RAISED: {a.get('reason')}")
    for r in rows:
        extra = " ".join(f"{k}={r[k]}" for k in ("handoffStatus", "verification", "failureMode") if r[k])
        print(f"{r['status']:<11} {r['type']:<10} {r['name']:<32} {r['branch']}  {extra}".rstrip())
    return 0


def cmd_tree(ws: Workspace, args, depth: int = 0) -> int:
    pad = "  " * depth
    print(f"{pad}[{ws.slug}] {ws.dir}")
    for t, r in _status_rows(ws):
        mark = "↻ " if t["type"] == "subplanner" else ""
        print(f"{pad}  {mark}{t['name']} ({t['type']}): {r['status']} {r.get('verification') or ''}".rstrip())
        if t["type"] == "subplanner" and r.get("worktree"):
            child = Path(r["worktree"]) / ".orchestrate" / t["name"]
            if (child / "plan.json").exists():
                cmd_tree(Workspace(child), args, depth + 2)
    return 0


def cmd_respawn(ws: Workspace, args) -> int:
    row = ws.row(args.task)
    if row["status"] == "running" and pid_alive(row.get("pid")):
        raise OrchError(f"{args.task} is still running; kill it first")
    row["status"] = "pending"
    ws.save()
    print(json.dumps({"task": args.task, "status": "pending", "attempts": row.get("attempts", 0)}))
    return 0


def _kill_row(ws: Workspace, name: str) -> None:
    row = ws.row(name)
    if row.get("status") != "running":
        return
    if row.get("backend") == "cli" and pid_alive(row.get("pid")):
        try:
            os.killpg(row["pid"], signal.SIGTERM)
        except ProcessLookupError:
            pass
    if row.get("type") == "subplanner" and row.get("worktree"):
        child = Path(row["worktree"]) / ".orchestrate" / name
        if (child / "plan.json").exists():
            cws = Workspace(child)
            for n in list(cws.state["tasks"]):
                _kill_row(cws, n)
            cws.save()
    row.update(status="cancelled", endedAt=now())


def cmd_kill(ws: Workspace, args) -> int:
    names = [n for n in ws.state["tasks"]] if args.all else [args.task]
    for n in names:
        _kill_row(ws, n)
    ws.save()
    print(json.dumps({"cancelled": names}))
    return 0


def cmd_andon(ws: Workspace, args) -> int:
    if args.action == "raise":
        if not args.reason:
            raise OrchError("--reason is required")
        ws.state["andon"] = {"raised": True, "reason": args.reason[:500], "raisedAt": now()}
    else:
        ws.state["andon"] = {"raised": False, "clearedAt": now(), "note": (args.note or "")[:500]}
    ws.save()
    print(json.dumps(ws.state["andon"]))
    return 0


def cmd_cleanup(ws: Workspace, args) -> int:
    removed = []
    for name, row in ws.state["tasks"].items():
        wt = row.get("worktree")
        if not wt or row.get("status") not in TERMINAL or not Path(wt).exists():
            continue
        git(["worktree", "remove", "--force", wt], ws.repo, check=False)
        removed.append(wt)
    git(["worktree", "prune"], ws.repo, check=False)
    print(json.dumps({"removedWorktrees": removed, "note": "branches are kept"}))
    return 0


def cmd_kickoff(args) -> int:
    repo = Path(git(["rev-parse", "--show-toplevel"], Path.cwd()))
    slug = args.slug or re.sub(r"[^a-z0-9]+", "-", args.goal.lower()).strip("-")[:40].strip("-") or "run"
    wsdir = repo / ".orchestrate" / slug
    if (wsdir / "state.json").exists() and not args.force:
        raise OrchError(f"{wsdir} already has a run; pass --force or pick another --slug")
    wsdir.mkdir(parents=True, exist_ok=True)
    base = args.base or git(["rev-parse", "--abbrev-ref", "HEAD"], repo)
    if not (wsdir / "plan.json").exists():
        write_json(wsdir / "plan.json", {
            "$schema": str(SKILL_DIR / "schemas" / "plan.schema.json"),
            "goal": args.goal, "rootSlug": slug, "baseBranch": base, "tasks": [],
        })
    Workspace(wsdir).save()
    prompt = render_template("root", {
        "goal": args.goal, "skillDir": str(SKILL_DIR), "workspace": str(wsdir),
        "loopHygiene": render_template("loop-hygiene", {"orch": ORCH}),
    })
    (wsdir / "prompts").mkdir(exist_ok=True)
    pfile = wsdir / "prompts" / "_root.md"
    pfile.write_text(prompt)
    if args.print_prompt:
        print(prompt)
        return 0
    plan = read_json(wsdir / "plan.json")
    cmd = [os.environ.get("ORCH_CLAUDE_BIN", "claude"), "-p", "--output-format", "json",
           "--model", args.model or DEFAULT_MODELS["root"],
           "--permission-mode", plan.get("permissionMode", "acceptEdits"),
           "--allowedTools", ",".join(plan.get("allowedTools", DEFAULT_ALLOWED_TOOLS))]
    log = wsdir / "logs" / "_root.json"
    err = wsdir / "logs" / "_root.stderr"
    with open(pfile) as fin, open(log, "w") as fout, open(err, "w") as ferr:
        p = subprocess.Popen(cmd, cwd=str(repo), stdin=fin, stdout=fout, stderr=ferr, start_new_session=True)
    print(json.dumps({"workspace": str(wsdir), "pid": p.pid, "log": str(log), "stderr": str(err),
                      "status": f"{ORCH} status {wsdir}"}, indent=2))
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="orch.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def ws_cmd(name, help_):
        p = sub.add_parser(name, help=help_)
        p.add_argument("workspace")
        return p

    p = ws_cmd("run", "spawn ready tasks as `claude -p` workers in worktrees; return on the next event")
    p.add_argument("--max-parallel", type=int)
    p.add_argument("--max-wait", type=int, default=540, help="seconds before returning while tasks still run (default 540)")
    p.add_argument("--poll", type=float, default=5.0)
    p.add_argument("--until-done", action="store_true", help="do not return on successful handoffs")
    p.add_argument("--dry-run", action="store_true")
    p = ws_cmd("prepare", "Agent-tool backend: create worktree + prompt for one task and mark it running")
    p.add_argument("task")
    p = ws_cmd("record", "Agent-tool backend: record a finished subagent's final message as the handoff")
    p.add_argument("task")
    p.add_argument("--file", help="file with the final message, or - for stdin (default: the handoff file the subagent wrote)")
    p.add_argument("--error", choices=list(SUGGESTIONS), help="record a failure handoff instead")
    p = ws_cmd("prompt", "render a task's prompt without spawning")
    p.add_argument("task")
    ws_cmd("validate", "validate plan.json")
    p = ws_cmd("status", "task table")
    p.add_argument("--json", action="store_true")
    ws_cmd("tree", "recursive tree including subplanner workspaces")
    p = ws_cmd("respawn", "reset a terminal task to pending (attempts are kept)")
    p.add_argument("task")
    p = ws_cmd("kill", "cancel a running task (and its subtree)")
    p.add_argument("task", nargs="?")
    p.add_argument("--all", action="store_true")
    p = ws_cmd("andon", "raise or clear the stop-the-line flag")
    p.add_argument("action", choices=["raise", "clear"])
    p.add_argument("--reason")
    p.add_argument("--note")
    ws_cmd("cleanup", "remove worktrees of terminal tasks (branches are kept)")
    p = sub.add_parser("kickoff", help="launch a detached `claude -p` root planner for a goal")
    p.add_argument("goal")
    p.add_argument("--slug")
    p.add_argument("--base")
    p.add_argument("--model")
    p.add_argument("--force", action="store_true")
    p.add_argument("--print-prompt", action="store_true")

    args = ap.parse_args(argv)
    try:
        if args.cmd == "kickoff":
            return cmd_kickoff(args)
        ws = Workspace(args.workspace)
        if args.cmd == "kill" and not (args.task or args.all):
            raise OrchError("kill needs a task name or --all")
        handler = {
            "run": cmd_run, "prepare": cmd_prepare, "record": cmd_record, "prompt": cmd_prompt,
            "validate": cmd_validate, "status": cmd_status, "tree": cmd_tree, "respawn": cmd_respawn,
            "kill": cmd_kill, "andon": cmd_andon, "cleanup": cmd_cleanup,
        }[args.cmd]
        return handler(ws, args)
    except OrchError as e:
        print(f"orch: {e}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
