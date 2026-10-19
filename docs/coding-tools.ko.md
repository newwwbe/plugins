# 코딩용 도구 정리: Arena · Ponytail · Graphify · Headroom · MarkItDown · Ruflo

모두 이 마켓플레이스(`newwwbe/plugins`)의 설치 스크립트 한 줄로 설치됩니다.

```bash
# macOS / Linux / WSL
curl -fsSL https://raw.githubusercontent.com/newwwbe/plugins/main/install.sh | bash
# 선택 항목(Ruflo, Headroom)까지
curl -fsSL https://raw.githubusercontent.com/newwwbe/plugins/main/install.sh | bash -s -- --with "ruflo headroom"
```

```powershell
# Windows
irm https://raw.githubusercontent.com/newwwbe/plugins/main/install.ps1 | iex
```

## 한눈에 보기

| 도구 | 종류 | 하는 일 | 기본 설치 | 사용법 |
|:--|:--|:--|:--|:--|
| Ponytail | 플러그인(스킬+훅) | 새 코드를 쓰기 전에 기존 코드·표준 라이브러리·플랫폼 기능부터 쓰게 함 | O | 자동 적용, `/ponytail lite\|full\|ultra\|off` |
| Arena | 플러그인(스킬) | 같은 과제를 여러 서브에이전트가 다른 전략으로 풀고 토너먼트로 하나만 남김 | O | `/arena-skill:arena <과제>` |
| MarkItDown | 플러그인(MCP) | PDF·Word·Excel·PPT·HTML·이미지·오디오·URL을 Markdown으로 변환 | O | "이 PDF 마크다운으로 바꿔서 요약해줘" |
| Graphify | CLI + 스킬 | 코드·문서 폴더를 지식 그래프로 만들어 구조 질문에 답함 | O | `/graphify .` |
| Ruflo | 플러그인 마켓플레이스 | 100개 이상 에이전트, 스웜 협업, 벡터 메모리, MCP 도구 300여 개 | 선택 | `--with ruflo` |
| Headroom | CLI(로컬 프록시) + 플러그인 | 도구 출력·로그·코드를 모델에 보내기 전에 압축해 토큰 절약 | 선택 | `--with headroom` |

## 도구별 설명

### Ponytail ([DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail), MIT)
"가장 게으른 시니어 개발자"처럼 행동하게 하는 규칙을 세션 시작 시 주입합니다. YAGNI, 표준 라이브러리 우선, 요청받지 않은 추상화 금지. `ponytail-review`(diff 검토), `ponytail-audit`(저장소 전체 점검)도 들어 있습니다. 턴마다 작업 기록을 `~/.config/ponytail/band/`에 CSV로 남기며, `claude plugin configure ponytail`에서 끌 수 있습니다.
**평가:** 코드 양을 줄이고 과설계를 막는 데 유용. 기본 설치.

### Arena ([Jakeschincariol/arena-skill](https://github.com/Jakeschincariol/arena-skill), MIT)
최대 100개의 서브에이전트가 각자 다른 전략 카드로 같은 과제를 풀고, 공격·방어·심판 대진으로 한 답만 남깁니다. 작업은 `.arena/` 안에서만 하므로 결과를 적용하기 전까지 파일이 바뀌지 않습니다.
**평가:** 어려운 설계·버그에 유용하지만 100개 모드는 서브에이전트 호출이 600회 가까이 됩니다. 평소엔 작은 규모로 실행하세요. 호출할 때만 동작하므로 기본 설치.

### MarkItDown ([microsoft/markitdown](https://github.com/microsoft/markitdown), MIT)
Microsoft의 문서→Markdown 변환기. 이 저장소의 `markitdown` 플러그인이 MCP 서버(`uvx markitdown-mcp`)를 등록하고, 도구 `convert_to_markdown(uri)` 하나를 제공합니다. 스펙 PDF, 엑셀 표, 회의록 등을 Claude가 바로 읽을 수 있게 됩니다. `uv`가 필요하며 설치 스크립트가 없으면 설치합니다.
**평가:** 가볍고 부작용 없음. 기본 설치.

### Graphify ([safishamsi/graphify](https://github.com/safishamsi/graphify), MIT)
`/graphify .`를 실행하면 tree-sitter로 코드를 로컬에서 파싱하고, 문서·이미지는 Claude로 개념을 뽑아 `graphify-out/`에 `graph.html`, `GRAPH_REPORT.md`, `graph.json`을 만듭니다. 이후 구조 질문을 그래프로 답해 큰 저장소에서 파일을 덜 읽습니다. PyPI 패키지 이름은 `graphifyy`(y 두 개)이고, `graphify install`이 `~/.claude/skills/graphify`와 CLAUDE.md 섹션, PreToolUse 훅을 추가합니다.
**평가:** 큰 코드베이스 파악에 유용. Claude Code 플러그인이 아니라 CLI라 설치 스크립트가 따로 설치합니다(`--no-tools`로 생략).

### Ruflo ([ruvnet/ruflo](https://github.com/ruvnet/ruflo), MIT, 옛 이름 Claude Flow)
Claude Code 위에 얹는 멀티 에이전트 오케스트레이션 계층. 자체 마켓플레이스에 플러그인 40여 개가 있고, 설치 스크립트는 그중 `ruflo-core`(MCP 서버, 기본 에이전트·스킬)와 `ruflo-swarm`(에이전트 팀, 워크트리 격리)만 설치합니다. 나머지는 `/plugin install <이름>@ruflo`로 추가하세요.
**평가:** 기능은 많지만 무겁고 훅과 MCP 도구가 모든 세션에 붙습니다. 첫 실행 때 MCP 서버가 패키지를 내려받느라 연결이 늦을 수 있습니다. 선택 설치.

### Headroom ([headroomlabs-ai/headroom](https://github.com/headroomlabs-ai/headroom), Apache-2.0)
도구 출력, 로그, JSON, 코드, 대화 기록을 모델에 보내기 전에 압축하는 로컬 프록시. 원본은 로컬에 보관하고 필요하면 되돌려 받습니다. 설치 스크립트는 `headroom-ai` CLI 설치 → `headroom init -g claude`(Claude Code가 프록시를 거치게 설정) → 프록시가 살아 있는지 확인하는 `headroom` 플러그인 순으로 설치합니다. 되돌리기: `headroom unwrap claude`.
**평가:** 토큰 절감 효과가 크다고 알려져 있으나(수치는 프로젝트 자체 발표), 모든 API 트래픽이 로컬 프록시를 거치게 바뀌므로 선택 설치.

## 다른 기기·환경에 적용하기

- **새 컴퓨터:** 위 한 줄 명령을 실행. 다시 실행하면 업데이트됩니다.
- **스크립트 없이:** `~/.claude/settings.json`에 README의 "Without the script" 블록을 넣으면 Claude Code가 다음 실행 때 플러그인을 받아 옵니다(Graphify CLI는 제외).
- **팀 저장소:** 같은 블록을 저장소의 `.claude/settings.json`에 커밋하면 그 저장소를 여는 모든 사람에게 적용됩니다.
- **Claude Code 웹(클라우드):** 환경 설정의 Setup script에 한 줄 설치 명령을 넣으세요.
