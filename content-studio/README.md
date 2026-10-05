# Content Studio

A CLI that produces a complete content package — research brief, structured
article, cover art, verified art direction, transcribed voiceover — using
**every Meta Model API capability** through the `meta-model-api` skill CLIs.

## Commands

| Command | API capability | What it does |
|---|---|---|
| `research <topic>` | Search grounding (`/responses` + `web_search`) | Live-researched brief, saved to `output/research.md` |
| `article <topic>` | Chat completions + `json_schema` | Strict-schema article JSON (`output/article.json`) |
| `cover <topic>` | Image generation (`muse-image-1.0`, ~$0.01) | 1024×1024 cover art (`output/cover.png`) |
| `describe <image>` | Image understanding (data-URI in chat) | Two-sentence critique + suitability score |
| `narrate <audio>` | Speech-to-text (`/asr/transcribe`) | Transcribed voiceover (`output/transcript.txt`) |
| `budget <file>` | Token counting (`/responses/input_tokens`) | Token count + cost estimate |
| `chat` | Responses API + `previous_response_id` | Interactive refinement with reasoning continuity |
| `tools <topic>` | Tool calling (function calling round-trip) | Model invokes a reading-time calculator |
| `models` | `/models` listing | Available models |

## Usage

```bash
./studio.py research "Meta AI glasses"
./studio.py article  "Meta AI glasses"
./studio.py cover    "Meta AI glasses"
./studio.py describe output/cover.png
./studio.py budget   output/research.md
./studio.py tools    "Meta AI glasses"
./studio.py chat
```

Voiceover pipeline example (uses the `tts` skill to make the audio, then the
Meta API to transcribe it):

```bash
tts speak --output output/voiceover.mp3 --text-stdin <<<"Your script here."
./studio.py narrate output/voiceover.mp3
```

## Notes

- Auth flows through the vaulted `meta-model-api` credential — no keys in code.
- `model-api-call` accepts `@payload.json` for large payloads (base64 images
  exceed the OS arg-length limit inline).
- Freebuff was connected and verified for interactive use; the build itself was
  done directly, since Freebuff is a TUI with no headless/scriptable mode.
