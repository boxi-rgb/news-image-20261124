#!/usr/bin/env python3
"""Draw a one-page newspaper front for 24 November 2026.

Everything is drawn from scratch with Pillow: no photos, no downloaded
artwork, no network access. Every text block is measured with textlength
first; if a block cannot fit its box the script raises instead of
drawing overflow, so a bad story can never ship silently.
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "entry.png")

W, H = 1024, 1024
MARGIN = 44
CONTENT_W = W - 2 * MARGIN  # 936

PAPER = (248, 244, 233)
INK = (22, 22, 22)
RED = (178, 32, 38)
GRAY = (98, 94, 86)

SERIF = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"
SERIF_BOLD = "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def load(path, size):
    return ImageFont.truetype(path, size)


def width_of(draw, text, fnt):
    return draw.textlength(text, font=fnt)


def wrap_text(draw, text, fnt, max_width):
    """Greedy word wrap. Raises if a single word is wider than max_width."""
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        if width_of(draw, current, fnt) > max_width:
            raise ValueError("single word too wide: %r" % current)
        for word in words[1:]:
            trial = current + " " + word
            if width_of(draw, trial, fnt) <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
                if width_of(draw, current, fnt) > max_width:
                    raise ValueError("single word too wide: %r" % current)
        lines.append(current)
    return lines


def fit_wrapped(draw, text, path, top, bottom, max_width, max_lines):
    """Largest size in [bottom, top] whose wrap fits max_lines.

    Returns (font, lines). Raises when even bottom overflows.
    """
    for size in range(top, bottom - 1, -1):
        fnt = load(path, size)
        lines = wrap_text(draw, text, fnt, max_width)
        if len(lines) <= max_lines:
            return fnt, lines
    raise ValueError("text does not fit in %d lines: %r" % (max_lines, text))


def fit_one_line(draw, text, path, top, bottom, max_width):
    """Largest size whose single line fits max_width. Raises on overflow."""
    for size in range(top, bottom - 1, -1):
        fnt = load(path, size)
        if width_of(draw, text, fnt) <= max_width:
            return fnt
    raise ValueError("text does not fit width %d: %r" % (max_width, text))


def tracked_width(draw, text, fnt, tracking):
    total = 0.0
    for ch in text:
        total += draw.textlength(ch, font=fnt) + tracking
    return total - tracking if text else 0.0


def draw_tracked_centred(draw, cx, y, text, fnt, fill, tracking=2):
    total = tracked_width(draw, text, fnt, tracking)
    x = cx - total / 2.0
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking


def draw_tracked_left(draw, x, y, text, fnt, fill, tracking=1.5):
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking


def hline(draw, x0, x1, y, width=2, fill=INK):
    draw.line([(x0, y), (x1, y)], fill=fill, width=width)


def draw_chip(draw, cx, cy, half):
    """Line-art processor chip: square body, inner die, pins, NVDA label."""
    # Pins on all four sides.
    pin_len = 16
    gap = 26
    for i in (-1, 0, 1):
        off = i * gap
        # Top and bottom pins.
        draw.line([(cx + off, cy - half - pin_len), (cx + off, cy - half)],
                  fill=INK, width=3)
        draw.line([(cx + off, cy + half), (cx + off, cy + half + pin_len)],
                  fill=INK, width=3)
        # Left and right pins.
        draw.line([(cx - half - pin_len, cy + off), (cx - half, cy + off)],
                  fill=INK, width=3)
        draw.line([(cx + half, cy + off), (cx + half + pin_len, cy + off)],
                  fill=INK, width=3)
    # Body and inner die.
    draw.rectangle([cx - half, cy - half, cx + half, cy + half],
                   outline=INK, width=3)
    inner = half - 22
    draw.rectangle([cx - inner, cy - inner, cx + inner, cy + inner],
                   outline=INK, width=2)
    # Red die dot in the middle.
    draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=RED)
    # Label under the chip.
    lfnt = load(SANS_BOLD, 15)
    label = "NVDA"
    lw = width_of(draw, label, lfnt)
    draw.text((cx - lw / 2, cy + half + pin_len + 4), label,
              font=lfnt, fill=GRAY)


LEAD_KICKER = "TECH  ·  SILICON VALLEY"
LEAD_HEADLINE = "HUANG IS BACK AT NVIDIA"
LEAD_SUMMARY = (
    "Eleven days after he resigned over affairs \u2014 one with a woman "
    "said to be a suspected Chinese spy \u2014 the board voted unanimously "
    "to restore Jensen Huang, after days of lobbying by President Trump. "
    "Shares leapt 33%.")
LEAD_CAPTION = "SHARES JUMP 33%"


def draw_lead(draw):
    x0 = MARGIN
    x1 = 660  # lead text column ends here
    y = 168
    kfnt = load(SANS_BOLD, 17)
    draw_tracked_left(draw, x0, y, LEAD_KICKER, kfnt, RED, tracking=2)
    y += 30
    hfnt, hlines = fit_wrapped(draw, LEAD_HEADLINE, SERIF_BOLD,
                               42, 34, x1 - x0, 2)
    lh = int(hfnt.size * 1.08)
    for line in hlines:
        draw.text((x0, y), line, font=hfnt, fill=INK)
        y += lh
    y += 8
    sfnt, slines = fit_wrapped(draw, LEAD_SUMMARY, SERIF, 19, 16, x1 - x0, 3)
    slh = int(sfnt.size * 1.32)
    for line in slines:
        draw.text((x0, y), line, font=sfnt, fill=INK)
        y += slh
    if y > 360:
        raise ValueError("lead block overflows its zone (bottom %d)" % y)
    # Divider and chip on the right.
    gx = 676
    draw.line([(gx, 172), (gx, 330)], fill=GRAY, width=1)
    draw_chip(draw, 830, 234, 62)
    cfnt = load(SANS_BOLD, 13)
    cw = width_of(draw, LEAD_CAPTION, cfnt)
    draw.text(((692 + 980 - cw) / 2, 336), LEAD_CAPTION,
              font=cfnt, fill=GRAY)


# (kicker, headline, body) — six cards, two columns by three rows.
STORIES = [
    ("POLAND  ·  NATO",
     "NATO SENDS AWACS TO POLAND AFTER MISSILE FALLS",
     "Three Russian Kh-101 missiles came down in Poland on Friday. NATO "
     "will forward-deploy an early-warning jet as allies weigh more "
     "defences."),
    ("IRAN  ·  QOM",
     "SINGER FLOGGED 74 TIMES FOR SINGING WITHOUT HIJAB",
     "Parastoo Ahmadi, 29, and four of her team were lashed in Qom over a "
     "2024 online concert. They also face two-year bans on performing and "
     "travel."),
    ("WASHINGTON  ·  AI",
     "TWO STATES SUE MUSK OVER GROK SEX IMAGES",
     "Virginia and Oregon say Grok turned photos of real people, including "
     "children, into sexual images. They seek penalties of $2,500 per "
     "violation."),
    ("WASHINGTON  ·  CONGRESS",
     "GOMEZ QUITS AFTER ETHICS PANEL FINDS MISCONDUCT",
     "Rep. Jimmy Gomez will resign on Dec. 1 after the House Ethics "
     "Committee found \u2018substantial evidence\u2019 of sexual misconduct "
     "toward a staffer."),
    ("CLIMATE  ·  ANTALYA",
     "COP31 FLOP BRINGS BLAME AND DESPAIR",
     "Australia\u2019s Chris Bowen faces calls to resign after the talks "
     "collapsed with no deal. Pacific nations said: \u2018We have been let "
     "down on all sides.\u2019"),
    ("UNITED NATIONS  ·  AI",
     "UN CHIEF WANTS GLOBAL AI SAFETY RULES IN A YEAR",
     "Ant\u00f3nio Guterres called for a multilateral framework for AI risk "
     "management, warning AI is driving \u2018the biggest transfer of "
     "power\u2019 in history."),
]

# (headline, rest) — three short items in the footer strip.
ALSO = [
    ("FACTORY FIRE TOLL AT 24",
     "About 30 workers still missing after the candy plant blaze."),
    ("ALCARAZ WINS ATP FINALS",
     "He beat world No. 1 Zverev 6-2, 7-6(7) in Turin."),
    ("HOUTHIS STRIKE RIYADH AGAIN",
     "Three missiles intercepted; the tallest tower was hit Thursday."),
]


def draw_story(draw, x, y, w, kicker, headline, body):
    hline(draw, x, x + w, y, width=2)
    ky = y + 8
    kfnt = load(SANS_BOLD, 14)
    draw_tracked_left(draw, x, ky, kicker, kfnt, RED, tracking=1.5)
    hy = ky + 24
    hfnt, hlines = fit_wrapped(draw, headline, SERIF_BOLD, 26, 19, w, 2)
    hlh = int(hfnt.size * 1.12)
    for line in hlines:
        draw.text((x, hy), line, font=hfnt, fill=RED)
        hy += hlh
    by = hy + 4
    bfnt, blines = fit_wrapped(draw, body, SERIF, 17, 13, w, 3)
    blh = int(bfnt.size * 1.26)
    for line in blines:
        draw.text((x, by), line, font=bfnt, fill=INK)
        by += blh
    return by


def draw_also(draw, y):
    hline(draw, MARGIN, W - MARGIN, y, width=2)
    fy = y + 12
    ffnt = load(SANS_BOLD, 16)
    draw_tracked_left(draw, MARGIN, fy, "ALSO TODAY", ffnt, RED, tracking=2)
    iy = fy + 28
    col_w = (CONTENT_W - 2 * 24) // 3  # 296
    for i, (lead, rest) in enumerate(ALSO):
        x = MARGIN + i * (col_w + 24)
        draw.rectangle([x, iy + 5, x + 8, iy + 13], fill=RED)
        tx = x + 16
        tw = col_w - 16
        lfnt, llines = fit_wrapped(draw, lead, SERIF_BOLD, 16, 13, tw, 1)
        draw.text((tx, iy), llines[0], font=lfnt, fill=INK)
        ry = iy + int(lfnt.size * 1.25)
        rfnt, rlines = fit_wrapped(draw, rest, SERIF, 16, 13, tw, 2)
        rlh = int(rfnt.size * 1.28)
        for line in rlines:
            draw.text((tx, ry), line, font=rfnt, fill=GRAY)
            ry += rlh
    return iy + 62


def main():
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    # Masthead.
    hline(draw, MARGIN, W - MARGIN, 26, width=3)
    mfnt = fit_one_line(draw, "THE WORLD IN ONE PICTURE",
                        SERIF_BOLD, 64, 40, CONTENT_W)
    mw = width_of(draw, "THE WORLD IN ONE PICTURE", mfnt)
    draw.text(((W - mw) / 2, 38), "THE WORLD IN ONE PICTURE",
              font=mfnt, fill=INK)
    hline(draw, MARGIN, W - MARGIN, 108, width=1)
    # Dateline.
    dfnt = load(SANS_BOLD, 18)
    draw_tracked_centred(draw, W / 2, 120,
                         "ONE DAY'S NEWS  ·  TUESDAY 24 NOVEMBER 2026",
                         dfnt, INK, tracking=2)
    # Double rule under the dateline.
    hline(draw, MARGIN, W - MARGIN, 148, width=3)
    hline(draw, MARGIN, W - MARGIN, 154, width=1)

    draw_lead(draw)

    # Rule above the story grid.
    hline(draw, MARGIN, W - MARGIN, 364, width=2)

    col_w = (CONTENT_W - 24) // 2  # 456
    row_h = 162
    row_gap = 10
    y0 = 380
    for idx, (kicker, headline, body) in enumerate(STORIES):
        col = idx % 2
        row = idx // 2
        x = MARGIN + col * (col_w + 24)
        y = y0 + row * (row_h + row_gap)
        bottom = draw_story(draw, x, y, col_w, kicker, headline, body)
        if bottom > y + row_h:
            raise ValueError("story %d overflows its row" % (idx + 1))

    footer_bottom = draw_also(draw, 898)
    hline(draw, MARGIN, W - MARGIN, 1004, width=3)
    if footer_bottom > 1002:
        raise ValueError("footer overflows the page")

    img.save(OUT, format="PNG", optimize=True)
    size = os.path.getsize(OUT)
    print("wrote %s (%dx%d, %d bytes)" % (OUT, W, H, size))
    if size > 1048576:
        raise ValueError("entry.png exceeds 1 MiB: %d bytes" % size)


if __name__ == "__main__":
    main()
