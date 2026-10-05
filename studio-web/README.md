# Studio Web

Web UI for the Content Studio, deployed on Vercel. Wraps every Meta Model API
capability behind API routes that proxy to `https://api.meta.ai/v1`.

## Routes

| Route | Method | Body | Proxies to |
|---|---|---|---|
| `/api/research` | POST | `{topic}` | `/responses` + `web_search` |
| `/api/article` | POST | `{topic}` | `/chat/completions` + `json_schema` |
| `/api/cover` | POST | `{topic}` | `/images/generations` (~$0.01) |
| `/api/describe` | POST | multipart `image` | `/chat/completions` with `image_url` |
| `/api/narrate` | POST | multipart `audio` | `/asr/transcribe` (WAV only) |
| `/api/budget` | POST | `{text}` | `/responses/input_tokens` |
| `/api/tools` | POST | `{topic, words}` | `/chat/completions` + function calling round-trip |
| `/api/chat` | POST | `{prompt, previousResponseId?}` | `/responses` with chaining |
| `/api/models` | GET | — | `/models` |

## API key

The app never sees a server-side key. Paste your Meta Model API key in the UI;
it's stored in `localStorage` and sent as the `x-meta-api-key` header, which
each route forwards as the Bearer token to `api.meta.ai`. Nothing secret is
committed to the repo.

## Deploy

Push to GitHub and connect the repo in Vercel (or use the Vercel CLI).
Long routes (research, cover, narrate) allow up to 60s via `vercel.json`
(`maxDuration`); on the Hobby plan that's the ceiling, so very slow
generations may time out — retry or upgrade the plan.

## Develop

```bash
npm install
npm run dev
```
