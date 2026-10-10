#!/usr/bin/env python
"""Generate the 16:9 hackathon cover (form field 4, recommended 380x216, ≤1MB).

Deterministic drawing (no network): teal field, brand heart+pulse motif,
product name, tagline, track line. Outputs cover.png at 2x for crispness.

Usage: python competition-tencent/generate_cover.py
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
W, H = 760, 432  # 2x of 380x216, still 16:9

TEAL_DARK = (13, 74, 70)
TEAL = (15, 118, 110)
TEAL_LIGHT = (153, 226, 219)
AMBER = (245, 158, 11)
WHITE = (255, 255, 255)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def heart_with_pulse(draw: ImageDraw.ImageDraw, cx: int, cy: int, s: float) -> None:
    """Parametric heart outline with a pulse line across it."""
    pts = []
    for i in range(200):
        t = math.pi * 2 * i / 200
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * s, cy - y * s))
    draw.polygon(pts, fill=TEAL_LIGHT)
    draw.line(pts + [pts[0]], fill=TEAL_DARK, width=3)
    # pulse
    py = cy + 1 * s
    seg = [
        (cx - 10 * s, py),
        (cx - 5 * s, py),
        (cx - 3 * s, py - 4 * s),
        (cx - 1 * s, py + 5 * s),
        (cx + 1.5 * s, py - 3 * s),
        (cx + 3 * s, py),
        (cx + 10 * s, py),
    ]
    draw.line(seg, fill=TEAL_DARK, width=max(3, int(1.2 * s)), joint="curve")


def main() -> None:
    img = Image.new("RGB", (W, H), TEAL_DARK)
    draw = ImageDraw.Draw(img)
    # subtle diagonal band
    draw.polygon([(0, H), (W * 0.55, H), (W, H * 0.35), (W, H), (0, H)], fill=TEAL)

    heart_with_pulse(draw, int(W * 0.2), int(H * 0.42), s=4.2)

    title = _font(58, bold=True)
    tagline = _font(24)
    track = _font(19)
    zh = _font(22)

    draw.text((W * 0.36, H * 0.24), "AI Healthier", font=title, fill=WHITE)
    draw.text((W * 0.36, H * 0.24 + 66), "Every Day", font=title, fill=AMBER)
    draw.text((W * 0.36, H * 0.24 + 150), "Small daily self-care, guided by AI", font=tagline, fill=TEAL_LIGHT)
    draw.text((W * 0.36, H * 0.24 + 186), "每天一点自我照护，AI 陪你坚持", font=zh, fill=TEAL_LIGHT)

    track_text = "Tencent Cloud AI CAN DO IT Hackathon SG 2026 · Healthcare Track"
    track_size = 19
    max_w = W * 0.36 - 24  # right margin
    while track_size > 12 and draw.textlength(track_text, font=_font(track_size)) > max_w:
        track_size -= 1
    draw.text((W * 0.36, H * 0.82), track_text, font=_font(track_size), fill=WHITE)

    out = HERE / "cover.png"
    img.save(out, optimize=True)
    size_kb = out.stat().st_size / 1024
    print(f"saved {out} ({W}x{H}, {size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
