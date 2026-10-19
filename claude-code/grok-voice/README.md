# Grok Voice for Claude Code

Claude Code port of the [Grok Voice](../../grok-voice/) Cursor plugin: four skills for building voice features into your app on xAI's Grok voice APIs — realtime speech-to-speech, speech-to-text dictation, text-to-speech read-aloud, and a debug loop for voice sessions.

## Installation

```
/plugin marketplace add newwwbe/plugins
/plugin install grok-voice@newwwbe
```

## Usage

| Command | What it does |
|:--------|:-------------|
| `/grok-voice:add-voice` | Build speech-to-speech into an app (or replace an STT-LLM-TTS cascade / OpenAI Realtime): realtime session, safe auth, app mic, waveform Voice Mode button. |
| `/grok-voice:add-dictation` | Speech-to-text: batch for a mic button or recorded audio (timestamps, diarization, subtitles); streaming through a relay for live text. |
| `/grok-voice:add-read-aloud` | Text-to-speech: batch MP3 for a speaker button; streaming PCM through a relay so audio starts before the reply finishes. |
| `/grok-voice:debug-voice` | Proposes a plan, installs a dev-only log pipeline (client logger → local NDJSON), then runs the fix loop: match your report to log signatures, fix one thing, re-test. |

The skills also load automatically when you ask to add Grok voice, dictation, or read-aloud to an app, or report that voice mode misbehaves. Icon convention across the skills: waveform = voice mode, microphone = dictation, speaker = read aloud.

## Requirements

- An xAI API key (`XAI_API_KEY`) for the app you are building; it stays server side.
- Network access to `docs.x.ai` (the skills read the live docs for model ids and event names) and `api.x.ai` when testing.

## Differences from the Cursor version

- Manifest lives in `.claude-plugin/plugin.json`; Cursor-only fields (`displayName`, `logo`, `category`, `tags`) and the logo assets are dropped.
- Slash-command cross-references use Claude Code's plugin namespace (`/add-voice` → `/grok-voice:add-voice`, etc.).
- "Cursor has no mic/speaker; wire the app, not the IDE" now reads "Claude Code has no mic/speaker; wire the app, not the coding agent." Otherwise the skill text is unchanged; it is host-agnostic.

## License

MIT
