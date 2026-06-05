"""Generate a square A/B/C/D legend image for the scoring screen.

Square so MAX shows it in full (a wide strip gets center-cropped in preview).
Run: python scripts/make_legend.py  -> assets/legend.png
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

W = H = 1080
BG = (237, 233, 216)
GREEN = (46, 77, 46)
DARK = (37, 57, 31)
GRAY = (110, 110, 110)

ARIAL = "/System/Library/Fonts/Supplemental/Arial.ttf"
ARIAL_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

ROWS = [
    ("A", "СОБСТВЕННИК", "Двигает бизнес, не делегируется"),
    ("B", "УПРАВЛЕНИЕ", "Нужная работа руководителя"),
    ("C", "ОПЕРАЦИОНКА", "Операционка, можно делегировать"),
    ("D", "СЛИВ", "Потеря времени и отвлечения"),
]


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    f_title = ImageFont.truetype(ARIAL_BOLD, 64)
    f_letter = ImageFont.truetype(ARIAL_BOLD, 84)
    f_name = ImageFont.truetype(ARIAL_BOLD, 52)
    f_desc = ImageFont.truetype(ARIAL, 34)

    # Header
    title = "ОЦЕНКА ДНЯ"
    tw = d.textlength(title, font=f_title)
    d.text(((W - tw) / 2, 56), title, font=f_title, fill=DARK)

    top = 210
    row_h = (H - top - 40) / len(ROWS)
    r = 66
    cx = 120
    for i, (letter, name, desc) in enumerate(ROWS):
        cy = int(top + row_h * i + row_h / 2)
        # circle
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN)
        lw = d.textlength(letter, font=f_letter)
        lbb = f_letter.getbbox(letter)
        d.text((cx - lw / 2, cy - (lbb[3] + lbb[1]) / 2), letter, font=f_letter, fill="white")
        # texts
        tx = cx + r + 50
        d.text((tx, cy - 52), name, font=f_name, fill=DARK)
        d.text((tx, cy + 8), desc, font=f_desc, fill=GRAY)

    img.save("assets/legend.png")
    print("saved assets/legend.png", img.size)


if __name__ == "__main__":
    main()
