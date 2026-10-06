#!/usr/bin/env python3
"""
Generate a neofetch-style terminal info card SVG for Ahan Ghosh.
Features:
- macOS/terminal title bar with dots: ahan@github: ~$ neofetch
- Staggered line-by-line slide/fade-in animation (CSS keyframes)
- Neofetch colored key-value pairs (OS, Host, Degree, Role, Languages, Tools, etc.)
- 8-color terminal palette blocks
- Sized 840x880 to pair symmetrically with ahan-ascii.svg in the README table.

Usage:
    python scripts/make_info_card.py [output.svg]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(HERE, "..", "info-card.svg")
OUT = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT

W, H = 840, 880
PAD = 36
TITLEBAR_H = 36

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"

# Neofetch color palette
CYAN = "#22d3ee"
GREEN = "#39d353"
YELLOW = "#f2cc60"
MAGENTA = "#d2a8ff"
BLUE = "#58a6ff"
RED = "#ff7b72"
WHITE = "#e6edf3"
MUTED = "#8b949e"
KEY_COLOR = "#58a6ff"

PALETTE_SWATCHES = [
    "#161b22", "#ff7b72", "#39d353", "#f2cc60",
    "#58a6ff", "#d2a8ff", "#22d3ee", "#e6edf3"
]

STATIC = bool(os.environ.get("STATIC"))

ROWS = [
    ("OS", "Arch Linux / GitHub Actions x86_64", WHITE),
    ("Host", "Alipurduar Govt. Engg. & Management College (AGEMC)", WHITE),
    ("Degree", "B.Tech in Electronics & Communication Engg. (ECE)", YELLOW),
    ("Role", "Software Developer · Web & Systems Enthusiast", CYAN),
    ("Focus", "Advanced Web Tech, Systems Programming & Open Source", GREEN),
    ("Languages", "JavaScript, TypeScript, Python, C++, HTML5, CSS3", WHITE),
    ("Frameworks", "React, Node.js, Express, Next.js", MAGENTA),
    ("Tools", "Git, GitHub, Linux, Bash, VS Code", WHITE),
    ("Goal", "Building impactful software & contributing to FOSS", GREEN),
    ("Fun Fact", "Debugs with console.log and not ashamed 😄", YELLOW),
    ("Contact", "ahanghosh72@gmail.com", CYAN),
    ("Links", "github.com/ahan-7 · in/ahan-ghosh-28246b308", BLUE),
]


def render_info_card():
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<style>',
        '@keyframes lineIn { from { opacity: 0; transform: translateX(-12px); } to { opacity: 1; transform: translateX(0); } }',
        '.ln { opacity: 0; animation: lineIn 0.4s ease-out forwards; }',
        '@media (prefers-reduced-motion: reduce) { .ln { opacity: 1 !important; transform: none !important; animation: none !important; } }',
        '</style>',
        '<defs>',
        f'<linearGradient id="cbg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>',
        '</defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#cbg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}" stroke-width="1"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]

    # Titlebar dots
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*18}" cy="{TITLEBAR_H/2}" r="5.5" fill="{dot}"/>')
    parts.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 5}" fill="{TITLE_TEXT}" font-size="13" '
                 f'text-anchor="middle">ahan@github: ~$ neofetch</text>')

    cur_y = TITLEBAR_H + 45
    delay = 0.1
    step_delay = 0.08

    def add_line(content_xml, custom_delay=None):
        nonlocal delay
        d = custom_delay if custom_delay is not None else delay
        if STATIC:
            parts.append(f'<g>{content_xml}</g>')
        else:
            parts.append(f'<g class="ln" style="animation-delay:{d:.2f}s">{content_xml}</g>')
        delay += step_delay

    # User Header
    hdr = (
        f'<text x="{PAD}" y="{cur_y}" font-size="22" font-weight="700">'
        f'<tspan fill="{CYAN}">ahan-7</tspan>'
        f'<tspan fill="{MUTED}">@</tspan>'
        f'<tspan fill="{GREEN}">AGEMC</tspan>'
        f'</text>'
    )
    add_line(hdr)

    cur_y += 18
    # Separator dashed line
    sep = f'<text x="{PAD}" y="{cur_y}" font-size="18" fill="{FRAME}">----------------------------------------</text>'
    add_line(sep)
    cur_y += 36

    # Neofetch rows
    for key, val, val_color in ROWS:
        row_content = (
            f'<text x="{PAD}" y="{cur_y}" font-size="18">'
            f'<tspan fill="{KEY_COLOR}" font-weight="700">{key:10s}</tspan>'
            f'<tspan fill="{MUTED}">  ➜  </tspan>'
            f'<tspan fill="{val_color}">{val}</tspan>'
            f'</text>'
        )
        add_line(row_content)
        cur_y += 42

    cur_y += 16
    # 8-color palette swatches
    swatches_content = [f'<text x="{PAD}" y="{cur_y}" font-size="16" fill="{MUTED}">Palette:</text>']
    swatch_size = 28
    swatch_gap = 10
    start_x = PAD + 95
    for idx, color in enumerate(PALETTE_SWATCHES):
        sx = start_x + idx * (swatch_size + swatch_gap)
        swatches_content.append(
            f'<rect x="{sx}" y="{cur_y - 20}" width="{swatch_size}" height="{swatch_size}" rx="4" fill="{color}"/>'
        )
    add_line("".join(swatches_content))

    # Bottom status / blinking prompt
    cur_y += 65
    prompt_y = H - 28
    parts.append(f'<line x1="0" y1="{H - 52}" x2="{W}" y2="{H - 52}" stroke="{FRAME}"/>')
    parts.append(f'<text x="{PAD}" y="{prompt_y}" font-size="14" fill="{MUTED}">'
                 f'ahan@github:~$ <tspan fill="{WHITE}">ready for new challenges</tspan></text>')
    cursor_x = PAD + len("ahan@github:~$ ready for new challenges ") * 8.4
    parts.append(f'<rect x="{cursor_x:.1f}" y="{prompt_y - 12}" width="8" height="15" fill="{CYAN}">'
                 f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/></rect>')

    parts.append('</svg>')
    svg = "".join(parts)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {OUT}: {W}x{H}, {len(svg)} bytes")


if __name__ == "__main__":
    render_info_card()
