#!/usr/bin/env python3
"""news-image-20261126: draw a newspaper front page summing up the world
news of Thursday 26 November 2026, and write it to /output/entry.png.

Pure standard library. Deterministic: no time, no randomness, no dict
iteration that affects output. A tiny PNG encoder (zlib + struct) writes
a truecolour RGB PNG, 1024x1024, with fixed filter bytes, so two runs
produce byte-identical output.
"""

import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (245, 239, 224)
INK = (17, 17, 17)
RED = (176, 32, 32)
BLUE = (31, 78, 121)
GREY = (122, 114, 96)
LIGHT = (232, 224, 205)
GOLD = (198, 142, 32)

# ---------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 bits, '1' = ink. Authored by hand.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
}

CHAR_W = 6  # 5 px glyph + 1 px gap, times scale
LINE_H = 8  # 7 px glyph + 1 px gap, times scale


def text_width(text, scale):
    return len(text) * CHAR_W * scale - scale


def draw_text(px, x, y, text, scale, color):
    """Draw uppercase text (lowercase is uppercased) at (x, y)."""
    cx = x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    fill_rect(px, cx + col * scale, y + row * scale,
                              scale, scale, color)
        cx += CHAR_W * scale
    return cx


def draw_text_centered(px, cx, y, text, scale, color):
    draw_text(px, cx - text_width(text, scale) // 2, y, text, scale, color)


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns list of lines fitting max_width px."""
    unit = CHAR_W * scale
    max_chars = max(1, (max_width + scale) // unit)
    lines = []
    for para in text.split("\n"):
        words = para.split(" ")
        line = ""
        for word in words:
            trial = word if not line else line + " " + word
            if len(trial) <= max_chars:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


# ------------------------------------------------------------------ canvas
def new_canvas():
    px = bytearray(W * H * 3)
    for i in range(0, len(px), 3):
        px[i] = PAPER[0]
        px[i + 1] = PAPER[1]
        px[i + 2] = PAPER[2]
    return px


def set_px(px, x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i] = color[0]
        px[i + 1] = color[1]
        px[i + 2] = color[2]


def fill_rect(px, x, y, w, h, color):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            px[i] = color[0]
            px[i + 1] = color[1]
            px[i + 2] = color[2]


def hline(px, x, y, w, color, thick=1):
    fill_rect(px, x, y, w, thick, color)


def vline(px, x, y, h, color, thick=1):
    fill_rect(px, x, y, thick, h, color)


def draw_line(px, x0, y0, x1, y1, color, thick=1):
    """Bresenham line with square thickness."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        fill_rect(px, x0 - thick // 2, y0 - thick // 2, thick, thick, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def fill_circle(px, cx, cy, r, color):
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5)
        hline(px, cx - dx, cy + dy, 2 * dx + 1, color)


def fill_poly(px, points, color):
    """Scanline fill for a simple polygon (list of (x, y))."""
    ys = [p[1] for p in points]
    for y in range(min(ys), max(ys) + 1):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                t = (y - y0) / (y1 - y0)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            x0 = int(xs[i] + 0.5)
            x1 = int(xs[i + 1] + 0.5)
            if x1 > x0:
                hline(px, x0, y, x1 - x0, color)


# ------------------------------------------------------------------- PNG
def png_bytes(px):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += px[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp)
            + chunk(b"IEND", b""))


# ------------------------------------------------------------- story blocks
def story_block(px, x, y, w, kicker, headlines, standfirst, icon):
    """A secondary story: red kicker, bold headlines, wrapped standfirst,
    and a small geometric icon drawn at the top right."""
    draw_text(px, x, y, kicker, 2, RED)
    hy = y + 22
    for line in headlines:
        draw_text(px, x, hy, line, 3, INK)
        hy += 26
    sy = hy + 6
    for line in wrap_text(standfirst, w, 2):
        draw_text(px, x, sy, line, 2, INK)
        sy += 18
    icon(px, x + w - 64, y + 4)
    return sy


# ------------------------------------------------------------------- icons
def icon_flame(px, x, y):
    fill_poly(px, [(x + 32, y), (x + 52, y + 26), (x + 58, y + 48),
                   (x + 44, y + 62), (x + 20, y + 62), (x + 6, y + 48),
                   (x + 12, y + 26)], RED)
    fill_poly(px, [(x + 32, y + 26), (x + 42, y + 40), (x + 38, y + 54),
                   (x + 26, y + 54), (x + 22, y + 40)], GOLD)


def icon_refinery(px, x, y):
    fill_rect(px, x + 6, y + 20, 52, 42, INK)
    fill_poly(px, [(x + 14, y + 20), (x + 22, y), (x + 30, y),
                   (x + 38, y + 20)], INK)
    fill_rect(px, x + 44, y + 8, 6, 54, INK)
    fill_rect(px, x + 12, y + 30, 8, 8, GOLD)
    fill_rect(px, x + 26, y + 30, 8, 8, GOLD)
    fill_rect(px, x + 40, y + 44, 8, 8, GOLD)


def icon_map_pin(px, x, y):
    fill_circle(px, x + 32, y + 22, 20, RED)
    fill_circle(px, x + 32, y + 22, 9, PAPER)
    fill_poly(px, [(x + 18, y + 34), (x + 46, y + 34), (x + 32, y + 62)],
              RED)


def icon_rocket(px, x, y):
    fill_poly(px, [(x + 32, y), (x + 44, y + 24), (x + 40, y + 48),
                   (x + 24, y + 48), (x + 20, y + 24)], BLUE)
    fill_circle(px, x + 32, y + 26, 6, PAPER)
    fill_poly(px, [(x + 20, y + 40), (x + 8, y + 58), (x + 20, y + 52)],
              RED)
    fill_poly(px, [(x + 44, y + 40), (x + 56, y + 58), (x + 44, y + 52)],
              RED)
    fill_poly(px, [(x + 26, y + 48), (x + 38, y + 48), (x + 32, y + 62)],
              GOLD)


def icon_planet(px, x, y):
    fill_circle(px, x + 32, y + 32, 26, GOLD)
    fill_circle(px, x + 24, y + 24, 5, (160, 110, 20))
    fill_circle(px, x + 40, y + 40, 7, (160, 110, 20))
    fill_circle(px, x + 38, y + 18, 4, (160, 110, 20))
    draw_line(px, x + 2, y + 44, x + 62, y + 20, BLUE, 3)


# -------------------------------------------------------------------- page
def build_page():
    px = new_canvas()
    mx = 36  # margin

    # Masthead
    draw_text_centered(px, W // 2, 30, "THE WORLD TODAY", 7, INK)
    hline(px, mx, 96, W - 2 * mx, INK, 4)
    hline(px, mx, 104, W - 2 * mx, INK, 1)
    draw_text(px, mx, 118, "VOL. I - NO. 330", 2, GREY)
    draw_text_centered(px, W // 2, 116, "THURSDAY 26 NOVEMBER 2026", 3, INK)
    draw_text(px, W - mx - text_width("PRICE: FREE", 2), 118,
              "PRICE: FREE", 2, GREY)
    hline(px, mx, 148, W - 2 * mx, INK, 1)
    hline(px, mx, 152, W - 2 * mx, INK, 4)

    # ---- Lead story: tariffs + market sell-off
    ly = 172
    draw_text(px, mx, ly, "WASHINGTON - TRADE WAR", 2, RED)
    draw_text(px, mx, ly + 26, "TARIFFS SHAKE", 6, INK)
    draw_text(px, mx, ly + 68, "WORLD MARKETS", 6, INK)
    lead = ("TRUMP PROPOSES NEW TARIFFS ON 14 PARTNERS - "
            "CHINA UP TO 40%. MARKETS TUMBLED: THE NASDAQ "
            "FELL ALMOST 4%, NVIDIA DOWN 8% AS AI FEARS SPREAD.")
    sy = ly + 122
    for line in wrap_text(lead, 560, 2):
        draw_text(px, mx, sy, line, 2, INK)
        sy += 18
    draw_text(px, mx, sy + 8, "S&P 500 -2.2%  -  NIKKEI -2.8%  -  BRENT $94.61",
              2, BLUE)

    # Chart panel: the Nasdaq slide
    cx0, cy0, cw, ch = 660, 172, 328, 236
    fill_rect(px, cx0, cy0, cw, ch, LIGHT)
    hline(px, cx0, cy0, cw, INK, 2)
    hline(px, cx0, cy0 + ch - 2, cw, INK, 2)
    vline(px, cx0, cy0, ch, INK, 2)
    vline(px, cx0 + cw - 2, cy0, ch, INK, 2)
    draw_text(px, cx0 + 14, cy0 + 12, "NASDAQ: THE DAY'S SLIDE", 2, INK)
    ox, oy = cx0 + 24, cy0 + 190
    vline(px, ox, cy0 + 40, 150, GREY, 1)
    hline(px, ox, oy, 260, GREY, 1)
    pts = [(ox + 0, cy0 + 52), (ox + 52, cy0 + 66), (ox + 104, cy0 + 96),
           (ox + 156, cy0 + 128), (ox + 208, cy0 + 168), (ox + 256, cy0 + 186)]
    for i in range(len(pts) - 1):
        draw_line(px, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                  RED, 4)
    for (pxx, pyy) in pts:
        fill_circle(px, pxx, pyy, 4, RED)
    draw_text(px, cx0 + 14, cy0 + ch - 28, "DOWN ALMOST 4% IN A DAY", 2, RED)

    hline(px, mx, 436, W - 2 * mx, INK, 2)

    # ---- Row 2: Cairo tanker fire / Houthi strikes on Saudi Arabia
    colw = 452
    story_block(px, mx, 458, colw, "EGYPT - DISASTER",
                ["31 KILLED IN CAIRO", "TANKER FIRE"],
                "A FUEL TANKER OVERTURNED ON THE RING ROAD "
                "IN GIZA AND EXPLODED. AT LEAST 31 DEAD, 21 "
                "HURT, DOZENS OF CARS BURNT.",
                icon_flame)
    story_block(px, 536, 458, colw, "YEMEN - SAUDI ARABIA",
                ["HOUTHIS HIT SAUDI", "OIL REFINERY"],
                "YEMEN'S HOUTHIS SAY THEY STRUCK THE RAS "
                "TANURA REFINERY AND SAUDI PORTS. OIL ROSE "
                "OVER 2% AS TENSIONS GREW.",
                icon_refinery)
    vline(px, 512, 458, 190, GREY, 1)
    hline(px, mx, 668, W - 2 * mx, INK, 2)

    # ---- Row 3: Gaza strike / North Korea nuclear call
    story_block(px, mx, 690, colw, "GAZA - CONFLICT",
                ["ISRAELI STRIKE", "KILLS HAMAS CHIEF"],
                "A STRIKE IN GAZA CITY KILLED HAMAS SECURITY "
                "CHIEF NAEEM ABU NAHEL AND SIX OTHERS, "
                "REPORTS SAY.",
                icon_map_pin)
    story_block(px, 536, 690, colw, "PYONGYANG - NUCLEAR",
                ["KIM ORDERS MORE", "NUCLEAR WEAPONS"],
                "KIM JONG UN CALLS FOR WIDER DEPLOYMENT OF "
                "TACTICAL NUCLEAR WEAPONS, STATE MEDIA KCNA "
                "REPORTS.",
                icon_rocket)
    vline(px, 512, 690, 190, GREY, 1)
    hline(px, mx, 900, W - 2 * mx, INK, 2)

    # ---- Bottom strip: science + sport
    by = 922
    draw_text(px, mx, by, "SCIENCE:", 2, RED)
    draw_text(px, mx + 112, by,
              "BEPICOLOMBO REACHES MERCURY ORBIT AFTER AN 8-YEAR JOURNEY",
              2, INK)
    draw_text(px, mx, by + 24, "SPORT:", 2, RED)
    draw_text(px, mx + 112, by + 24,
              "CHESS: GUKESH DRAWS GAME 2 WITH SINDAROV IN GENEVA",
              2, INK)
    icon_planet(px, W - mx - 64, by - 6)
    hline(px, mx, 986, W - 2 * mx, INK, 4)
    draw_text_centered(px, W // 2, 996,
                       "ALL THE NEWS THAT FITS - 26 NOVEMBER 2026", 2, GREY)
    return px


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    data = png_bytes(build_page())
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
