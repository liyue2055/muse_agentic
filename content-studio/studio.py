#!/usr/bin/env python3
"""Content Studio — a CLI that produces a complete content package using every
Meta Model API capability.

Each subcommand maps to one API skill:

  research <topic>    Search grounding (Responses API + web_search)
  article <topic>     Structured article as JSON (chat completions + json_schema)
  cover <topic>       Cover art (images/generations, muse-image-1.0, ~$0.01)
  describe <image>    Verify the cover (image understanding via chat completions)
  narrate <audio>     Transcribe a voiceover (asr/transcribe)
  budget <file>       Token count + cost estimate (responses/input_tokens)
  chat                Interactive refinement with reasoning continuity (Responses + previous_response_id)
  tools <topic>       Tool-calling demo: model invokes a reading-time calculator
  models              List available models

All calls go through ~/workspace/skills/meta-model-api/bin/ CLIs, which use
the vaulted API credential. Nothing here handles raw keys.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

BIN = os.path.expanduser("~/workspace/skills/meta-model-api/bin")
OUT = os.path.expanduser("~/workspace/content-studio/output")
os.makedirs(OUT, exist_ok=True)


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def sh(cmd: list[str]) -> str:
    r = run(cmd)
    if r.returncode != 0:
        print(r.stderr.strip() or r.stdout.strip(), file=sys.stderr)
        sys.exit(1)
    return r.stdout.strip()


def cmd_research(topic: str):
    """Search-grounded research brief."""
    print(f"Researching '{topic}' with live web search...")
    payload = {
        "model": "muse-spark-1.3",
        "input": (f"Write a concise research brief on: {topic}. "
                  f"Cover: what it is, why it matters now, 3 key facts."),
        "tools": [{"type": "web_search"}],
    }
    out = sh([f"{BIN}/model-api-call", "POST", "/responses", json.dumps(payload)])
    data = json.loads(out)
    text = "".join(c.get("text", "") for i in data.get("output", [])
                   for c in i.get("content", []) if c.get("type") == "output_text")
    path = f"{OUT}/research.md"
    open(path, "w").write(f"# Research: {topic}\n\n{text}\n")
    print(f"Saved {path}\n")
    print(text[:1200])


def cmd_article(topic: str):
    """Structured article JSON via json_schema."""
    print(f"Writing structured article on '{topic}'...")
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "subtitle": {"type": "string"},
            "sections": {"type": "array", "items": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["heading", "body"],
                "additionalProperties": False,
            }},
            "takeaways": {"type": "array", "items": {"type": "string"}},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["title", "subtitle", "sections", "takeaways", "tags"],
        "additionalProperties": False,
    }
    payload = {
        "model": "muse-spark-1.3",
        "messages": [{"role": "user",
                      "content": f"Write a short engaging article about: {topic}"}],
        "reasoning_effort": "low",
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": "article", "schema": schema,
                                            "strict": True}},
    }
    out = sh([f"{BIN}/model-api-call", "POST", "/chat/completions",
              json.dumps(payload)])
    article = json.loads(json.loads(out)["choices"][0]["message"]["content"])
    path = f"{OUT}/article.json"
    json.dump(article, open(path, "w"), indent=2)
    print(f"Saved {path}")
    print(f"Title: {article['title']}")
    print(f"Sections: {len(article['sections'])}, "
          f"takeaways: {len(article['takeaways'])}")


def cmd_cover(topic: str):
    """Generate cover art (~$0.01)."""
    print(f"Generating cover art for '{topic}'...")
    path = f"{OUT}/cover.png"
    sh([f"{BIN}/model-api-images",
        f"editorial cover illustration for an article about {topic}, "
        f"bold minimalist style, no text",
        "--out", path, "--size", "1024x1024"])
    print(f"Saved {path}")


def cmd_describe(image: str):
    """Describe/verify an image (image understanding)."""
    import base64
    import tempfile
    b64 = base64.b64encode(open(image, "rb").read()).decode()
    payload = {
        "model": "muse-spark-1.3",
        "reasoning_effort": "minimal",
        "max_tokens": 300,
        "messages": [{"role": "user", "content": [
            {"type": "text",
             "text": "Is this a suitable cover image for an article? "
                     "Describe it in two sentences and give a 1-10 suitability score."},
            {"type": "image_url",
             "image_url": {"url": "data:image/png;base64," + b64}},
        ]}],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(payload, fh)
        pfile = fh.name
    out = sh([f"{BIN}/model-api-call", "POST", "/chat/completions", "@" + pfile])
    os.unlink(pfile)
    print(json.loads(out)["choices"][0]["message"]["content"])


def cmd_narrate(audio: str):
    """Transcribe a voiceover file."""
    print(f"Transcribing {audio}...")
    text = sh([f"{BIN}/model-api-transcribe", audio])
    path = f"{OUT}/transcript.txt"
    open(path, "w").write(text + "\n")
    print(f"Saved {path}\n{text[:500]}")


def cmd_budget(path: str):
    """Token count + cost estimate for a text file."""
    text = open(path).read()
    out = sh([f"{BIN}/model-api-call", "POST", "/responses/input_tokens",
              json.dumps({"model": "muse-spark-1.3", "input": text})])
    n = json.loads(out)["input_tokens"]
    # muse-spark-1.3 standard tier: ~$1.25/1M input tokens (see capabilities doc)
    print(f"Input tokens: {n:,}  (~${n / 1e6 * 1.25:.4f} at standard tier)")


def cmd_tools(topic: str):
    """Tool-calling demo: the model invokes a reading-time calculator."""
    import math
    print("Asking the model to compute reading time via a tool call...")
    payload = {
        "model": "muse-spark-1.3",
        "messages": [{"role": "user", "content":
                      f"An article about {topic} is 1,850 words. Use the "
                      f"reading_time tool to tell me how long it takes to read."}],
        "reasoning_effort": "minimal",
        "tool_choice": "auto",
        "tools": [{"type": "function", "function": {
            "name": "reading_time",
            "description": "Estimate reading time in minutes for a word count",
            "parameters": {"type": "object",
                           "properties": {"words": {"type": "integer"}},
                           "required": ["words"], "additionalProperties": False}}}],
    }
    out = sh([f"{BIN}/model-api-call", "POST", "/chat/completions",
              json.dumps(payload)])
    msg = json.loads(out)["choices"][0]["message"]
    calls = msg.get("tool_calls") or []
    if not calls:
        print("Model answered directly:", msg.get("content"))
        return
    for c in calls:
        args = json.loads(c["function"]["arguments"])
        minutes = math.ceil(args["words"] / 200)
        print(f"Tool call: {c['function']['name']}({args}) -> {minutes} min")
    # Feed the result back for a natural answer
    payload["messages"].append(msg)
    for c in calls:
        args = json.loads(c["function"]["arguments"])
        payload["messages"].append({
            "role": "tool", "tool_call_id": c["id"],
            "content": json.dumps({"minutes": math.ceil(args["words"] / 200)}),
        })
    out2 = sh([f"{BIN}/model-api-call", "POST", "/chat/completions",
               json.dumps(payload)])
    print("Model:", json.loads(out2)["choices"][0]["message"]["content"])


def cmd_models():
    print(sh([f"{BIN}/model-api-models"]))


def cmd_chat():
    """Interactive refinement loop with reasoning continuity."""
    print("Studio chat — reasoning carries across turns. Empty line quits.")
    prev = None
    while True:
        try:
            prompt = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not prompt:
            break
        args = [f"{BIN}/model-api-responses", prompt]
        if prev:
            args += ["--prev", prev]
        r = run(args)
        if r.returncode != 0:
            print(r.stderr.strip(), file=sys.stderr)
            continue
        lines = r.stdout.strip().split("\n")
        prev = lines[0].split(":", 1)[1] if lines[0].startswith("RESPONSE_ID:") else None
        print("studio>", "\n".join(lines[1:]))


COMMANDS = {
    "research": (cmd_research, "<topic>"),
    "article": (cmd_article, "<topic>"),
    "cover": (cmd_cover, "<topic>"),
    "describe": (cmd_describe, "<image.png>"),
    "narrate": (cmd_narrate, "<audio file>"),
    "budget": (cmd_budget, "<text file>"),
    "tools": (cmd_tools, "<topic>"),
    "chat": (lambda _: cmd_chat(), ""),
    "models": (lambda _: cmd_models(), ""),
}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in COMMANDS:
        print("usage: studio.py <command> [args]\n")
        for name, (_, usage) in COMMANDS.items():
            print(f"  {name:10} {usage}")
        return 2
    fn, _ = COMMANDS[argv[1]]
    fn(" ".join(argv[2:]) if argv[1] != "chat" and argv[1] != "models" else "")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
