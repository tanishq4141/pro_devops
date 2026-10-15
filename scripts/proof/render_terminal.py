"""Render captured command output as a terminal-style PNG.

Usage: python render_terminal.py OUTPUT.png "window title" INPUT.txt [--width 1100]

The input file holds the *real* output of a command (captured with
`cmd 2>&1 | tee file`); this script only draws it so it can be attached
as a screenshot for grading.
"""
import argparse
import html
import os
import re

from playwright.sync_api import sync_playwright

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
RULES = [
    (re.compile(r"\b(PASSED|passed|Running|Ready|READY|UP|deployed|Bound|True|Complete!|Success|succeeded|no changes|0 failures)\b"), "ok"),
    (re.compile(r"\b(FAILED|failed|Error|ERROR|ErrImagePull|ImagePullBackOff|CrashLoopBackOff|DOWN|CRITICAL)\b"), "bad"),
    (re.compile(r"\b(WARN|WARNING|warning|Pending|HIGH|MEDIUM)\b"), "warn"),
]


def colorize(line: str) -> str:
    if line.startswith("$ "):
        return f'<span class="prompt">$</span> <span class="cmd">{html.escape(line[2:])}</span>'
    out = html.escape(line)
    for pattern, cls in RULES:
        out = pattern.sub(lambda m: f'<span class="{cls}">{m.group(0)}</span>', out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("output")
    ap.add_argument("title")
    ap.add_argument("input")
    ap.add_argument("--width", type=int, default=1100)
    args = ap.parse_args()

    text = ANSI.sub("", open(args.input, encoding="utf-8", errors="replace").read()).rstrip("\n")
    body = "\n".join(colorize(l) for l in text.splitlines())
    page = f"""<!doctype html><meta charset="utf-8"><style>
      body {{ margin:0; background:#e8ecf2; padding:24px; font-family: ui-sans-serif, system-ui; }}
      .win {{ background:#0d1117; border-radius:10px; box-shadow:0 10px 30px rgba(0,0,0,.25); overflow:hidden; }}
      .bar {{ background:#1f2630; color:#9aa7b8; font-size:13px; padding:9px 14px; display:flex; gap:8px; align-items:center; }}
      .bar i {{ width:12px; height:12px; border-radius:50%; display:inline-block; }}
      .bar span {{ margin-left:10px; }}
      pre {{ margin:0; padding:16px 18px; color:#d6deeb; font: 13px/1.5 "DejaVu Sans Mono", Menlo, Consolas, monospace; white-space:pre-wrap; word-break:break-all; }}
      .prompt {{ color:#7ee787; }} .cmd {{ color:#ffffff; font-weight:bold; }}
      .ok {{ color:#3fb950; }} .bad {{ color:#ff7b72; }} .warn {{ color:#e3b341; }}
    </style><div class="win"><div class="bar"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i><span>{html.escape(args.title)}</span></div><pre>{body}</pre></div>"""

    exe = os.environ.get("CHROMIUM_PATH")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        pg = browser.new_page(viewport={"width": args.width, "height": 400}, device_scale_factor=1)
        pg.set_content(page)
        pg.locator(".win").screenshot(path=args.output)
        browser.close()


if __name__ == "__main__":
    main()
