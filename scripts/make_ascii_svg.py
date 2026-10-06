#!/usr/bin/env python3
"""
Convert a portrait photo into a CLEAN, monochrome ASCII-art SVG that "types"
itself in like a terminal, then holds.

Monochrome is deliberate -- per-character rainbow color makes ASCII look noisy.
One fill color + a good density ramp + high contrast (so background washes out to blank)
reads as neat, legible, and striking.

GitHub renders SVGs embedded via <img> and runs their SMIL animations.
Each row is revealed with a left-to-right clip wipe plus a small block cursor
riding the wipe edge, staggered top -> bottom, so the whole portrait prints once and freezes.
"""
import html
import os
import sys
from PIL import Image, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SRC = os.path.join(HERE, "..", "source-prepped.png")
DEFAULT_OUT = os.path.join(HERE, "..", "ahan-ascii.svg")

SRC = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
OUT = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT

# Columns determine character resolution across ART_W
COLS = int(os.environ.get("COLS", 140))
ART_W_TARGET = 800
CELL_W = ART_W_TARGET / COLS
CELL_H = CELL_W * 15 / 8
ROWS = round(COLS * 8 / 15)
RAMP = " .`:-=+*cs#%@"  # bright(sparse) -> dark(dense); leading space clears bg

CONTRAST = 1.08
BRIGHTNESS = 1.0
GAMMA = 1.15
SHARPEN = False
WHITE_FLOOR = 0.82    # luminance above this is forced to blank space

PAD = 20
TITLEBAR_H = 30
STATUS_H = 30
ART_W = COLS * CELL_W
ART_H = ROWS * CELL_H
CANVAS_W = 840
CANVAS_H = 880

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"       # single monochrome ascii color
CURSOR = "#c9d1d9"

# reveal timing: raster sweep down over ~5.5s
TOTAL_PRINT_TIME = 5.5
ROW_DUR = TOTAL_PRINT_TIME / ROWS
STAGGER = ROW_DUR

STATIC = bool(os.environ.get("STATIC"))


def generate_ascii_svg():
    if not os.path.exists(SRC):
        print(f"Error: {SRC} does not exist. Run prep_photo.py first.", file=sys.stderr)
        sys.exit(1)

    # 1. Sample image into grayscale character grid
    im = Image.open(SRC).convert("L")
    if SHARPEN:
        im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=140, threshold=2))
    im = ImageEnhance.Brightness(im).enhance(BRIGHTNESS)
    im = ImageEnhance.Contrast(im).enhance(CONTRAST)
    im = im.resize((COLS, ROWS), Image.Resampling.LANCZOS)
    px = im.load()

    rows_txt = []
    for y in range(ROWS):
        chars = []
        for x in range(COLS):
            lum = px[x, y] / 255.0
            lum = pow(lum, GAMMA)
            if lum >= WHITE_FLOOR:
                chars.append(" ")
                continue
            idx = int((1.0 - lum) * (len(RAMP) - 1) + 0.5)
            idx = max(0, min(len(RAMP) - 1, idx))
            chars.append(RAMP[idx])
        rows_txt.append("".join(chars))

    art_x = (CANVAS_W - ART_W) / 2
    art_top = TITLEBAR_H + ((CANVAS_H - TITLEBAR_H - STATUS_H - ART_H) / 2)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
        f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<defs>'
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
        f'</linearGradient></defs>',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" fill="none" stroke="{FRAME}" stroke-width="1"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]

    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
    parts.append(f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
                 f'text-anchor="middle">ahan@github: ~$ ./portrait.sh</text>')

    font_size = CELL_H * 0.86
    for ry, line in enumerate(rows_txt):
        y = art_top + ry * CELL_H + CELL_H * 0.74
        row_y = art_top + ry * CELL_H
        delay = ry * STAGGER
        safe = html.escape(line)
        text = (f'<text xml:space="preserve" x="{art_x:.1f}" y="{y:.1f}" fill="{INK}" '
                f'font-size="{font_size:.1f}" textLength="{ART_W:.1f}" lengthAdjust="spacing">{safe}</text>')

        if STATIC:
            parts.append(text)
            continue

        parts.append(
            f'<clipPath id="r{ry}"><rect x="{art_x:.1f}" y="{row_y:.1f}" height="{CELL_H:.1f}" width="0">'
            f'<animate attributeName="width" from="0" to="{ART_W:.1f}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.2f}s" fill="freeze"/></rect></clipPath>'
        )
        parts.append(f'<g clip-path="url(#r{ry})">{text}</g>')
        parts.append(
            f'<rect y="{row_y+1:.1f}" width="{CELL_W:.1f}" height="{CELL_H-2:.1f}" fill="{CURSOR}" opacity="0">'
            f'<animate attributeName="x" from="{art_x:.1f}" to="{art_x+ART_W:.1f}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>'
        )

    # Status line with blinking cursor
    status_line_y = CANVAS_H - STATUS_H
    status_y = status_line_y + 19
    parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}"/>')
    prompt_str = "ahan@github:~$ whoami "
    name_str = "Ahan Ghosh"
    parts.append(f'<text x="{PAD}" y="{status_y:.1f}" fill="{TITLE_TEXT}" font-size="13">'
                 f'{prompt_str}<tspan fill="{INK}">{name_str}</tspan></text>')
    status_chars = len(prompt_str + name_str + " ")
    cursor_x = PAD + status_chars * 13 * 0.60
    parts.append(f'<rect x="{cursor_x:.1f}" y="{status_y-12:.1f}" width="8" height="14" fill="{INK}">'
                 f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
                 f'dur="1s" repeatCount="indefinite"/></rect>')

    parts.append("</svg>")
    svg = "".join(parts)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {OUT}: {CANVAS_W}x{CANVAS_H}, {len(svg)} bytes")


if __name__ == "__main__":
    generate_ascii_svg()
