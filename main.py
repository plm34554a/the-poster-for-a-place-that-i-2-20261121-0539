#!/usr/bin/env python3
"""LUMARELLE - a travel poster for a place that does not exist.

Draws a 1024x1024 travel poster with pure stdlib: a twilight lagoon where
lantern-islands drift under twin moons. Deterministic: same bytes every run.
Writes to $OUTPUT_DIR/entry.png (default /output/entry.png).
"""
import os
import struct
import zlib

W = 1024
H = 1024

# --- palette (purposeful, 5 colours + tints) ---
INDIGO = (22, 34, 79)      # night sky top
VIOLET = (91, 75, 138)     # dusk band
PEACH = (245, 165, 92)     # horizon glow
TEAL = (30, 111, 122)      # lagoon
DEEP = (14, 58, 74)        # deep water
CREAM = (255, 243, 214)    # type + moonlight
AMBER = (255, 176, 66)     # lantern light
INK = (16, 24, 54)         # island silhouettes

# --- pixel buffer ---
px = bytearray(W * H * 3)


def _lerp(a, b, t):
    return int(a + (b - a) * t)


def _mix(c1, c2, t):
    return (_lerp(c1[0], c2[0], t), _lerp(c1[1], c2[1], t), _lerp(c1[2], c2[2], t))


def fill_rect(x0, y0, x1, y1, col):
    x0 = max(0, x0); y0 = max(0, y0)
    x1 = min(W, x1); y1 = min(H, y1)
    if x0 >= x1 or y0 >= y1:
        return
    row = bytes(col) * (x1 - x0)
    for y in range(y0, y1):
        i = (y * W + x0) * 3
        px[i:i + len(row)] = row


def hline(y, x0, x1, col):
    if 0 <= y < H:
        fill_rect(x0, y, x1, y + 1, col)


def disc(cx, cy, r, col):
    """Filled circle, clipped."""
    for dy in range(-r, r + 1):
        y = cy + dy
        if y < 0 or y >= H:
            continue
        dx = int((r * r - dy * dy) ** 0.5)
        fill_rect(cx - dx, y, cx + dx + 1, y + 1, col)


def ellipse(cx, cy, rx, ry, col):
    for dy in range(-ry, ry + 1):
        y = cy + dy
        if y < 0 or y >= H:
            continue
        t = 1.0 - (dy * dy) / float(ry * ry)
        dx = int(rx * (t ** 0.5))
        fill_rect(cx - dx, y, cx + dx + 1, y + 1, col)


def glow(cx, cy, r, col, steps=5):
    """Soft radial glow: concentric discs fading toward the sky colour."""
    for k in range(steps, 0, -1):
        t = k / float(steps)
        rr = int(r * t)
        # blend lantern colour toward the local sky tone
        c = _mix(col, (120, 90, 120), 1.0 - t * 0.55)
        disc(cx, cy, rr, c)


# --- sky: vertical gradient indigo -> violet -> peach ---
HORIZON = 560
for y in range(HORIZON):
    if y < 300:
        t = y / 300.0
        c = _mix(INDIGO, VIOLET, t)
    else:
        t = (y - 300) / 260.0
        c = _mix(VIOLET, PEACH, t)
    fill_rect(0, y, W, y + 1, c)

# --- stars (deterministic) ---
seed = 1234567


def rnd():
    global seed
    seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
    return seed / 0x7FFFFFFF


for _ in range(140):
    sx = int(rnd() * W)
    sy = int(rnd() * 330)
    if rnd() < 0.75:
        fill_rect(sx, sy, sx + 2, sy + 2, CREAM)
    else:
        disc(sx, sy, 2, CREAM)

# --- twin moons with glow (kept clear of the title, in the dusk band) ---
glow(850, 330, 70, (255, 220, 160), steps=6)
disc(850, 330, 40, (255, 244, 214))
disc(864, 320, 32, (246, 226, 178))
glow(150, 300, 48, (255, 220, 160), steps=5)
disc(150, 300, 26, (255, 244, 214))

# --- sea: teal gradient with a warm reflection band ---
for y in range(HORIZON, H):
    t = (y - HORIZON) / float(H - HORIZON)
    c = _mix(TEAL, DEEP, t)
    # warm sunset reflection near the horizon
    if y < HORIZON + 90:
        c = _mix(c, PEACH, (1.0 - (y - HORIZON) / 90.0) * 0.45)
    fill_rect(0, y, W, y + 1, c)

# moonlight path on the water: short staggered glints under the big moon
for k in range(14):
    y = HORIZON + 16 + k * 16
    wdt = 18 + (k % 3) * 8
    off = ((k * 37) % 41) - 20
    hline(y, 850 - wdt + off, 850 + wdt + off, _mix(PEACH, CREAM, 0.4))

# gentle wave lines
for k in range(18):
    y = HORIZON + 120 + k * 20
    x0 = int(rnd() * 700)
    hline(y, x0, x0 + 60 + int(rnd() * 120), _mix(TEAL, CREAM, 0.25))

# --- birds ---
def bird(x, y, s):
    for dx in range(-s, s + 1):
        yy = y + abs(dx) // 2
        fill_rect(x + dx, yy, x + dx + 2, yy + 2, INK)


bird(300, 250, 12)
bird(360, 225, 9)
bird(640, 300, 10)
bird(700, 270, 7)

# --- lantern islands (the landmark): floating islands with glowing lanterns ---
def lantern(x, y, r=7):
    glow(x, y, r + 10, AMBER, steps=4)
    disc(x, y, r, AMBER)
    disc(x, y, r - 3, (255, 224, 150))


def island(cx, cy, rx, ry, lanterns):
    ellipse(cx, cy, rx, ry, INK)
    # little hut roofs on the island
    for hx, hw, hh in lanterns:
        fill_rect(hx - hw, cy - ry - hh, hx + hw, cy - ry + 2, INK)
        # triangular roof
        for k in range(hh // 2):
            fill_rect(hx - hw - k, cy - ry - hh - k, hx + hw + k, cy - ry - hh - k + 1, INK)
    for hx, hw, hh in lanterns:
        lantern(hx, cy - ry - hh - 8)


# far small islands
island(150, 640, 110, 26, [(110, 14, 16), (180, 12, 12)])
island(880, 620, 120, 28, [(840, 14, 16), (920, 12, 12)])
# central hero island: the great lantern-island of Lumarelle
island(512, 700, 260, 58, [(400, 26, 34), (512, 30, 44), (624, 26, 34)])
# tall lantern spire on the hero island
fill_rect(504, 560, 520, 660, INK)
for k in range(10):
    fill_rect(500 - k, 552 - k, 524 + k, 552 - k + 1, INK)
lantern(512, 540, 12)
lantern(512, 500, 9)
# reflections of the lanterns in the water
for lx in (400, 512, 624, 110, 180, 840, 920):
    for k in range(6):
        y = 760 + k * 12
        wdt = 8 - k
        if wdt > 0:
            hline(y, lx - wdt, lx + wdt, _mix(AMBER, TEAL, 0.35 + k * 0.1))

# --- sailboats ---
def boat(x, y, s):
    # hull
    for k in range(10):
        fill_rect(x - s + k, y + k, x + s - k, y + k + 1, INK)
    # mast + sail
    fill_rect(x, y - 3 * s, x + 2, y, INK)
    for k in range(3 * s):
        fill_rect(x + 2, y - 3 * s + k, x + 2 + (3 * s - k) // 2, y - 3 * s + k + 1, CREAM)


boat(250, 830, 26)
boat(770, 880, 20)

# --- 5x7 bitmap letterfont (capitals + space) ---
FONT = {
    'A': ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    'B': ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    'C': ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    'D': ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    'E': ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    'F': ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    'G': ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    'H': ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    'I': ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    'J': ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    'K': ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    'L': ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    'M': ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    'N': ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    'O': ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    'P': ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    'Q': ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    'R': ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    'S': ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    'T': ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    'U': ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    'V': ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    'W': ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    'X': ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    'Y': ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    'Z': ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    ' ': ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}


def text_width(s, scale, gap):
    return len(s) * (5 * scale + gap) - gap


def draw_text(s, x, y, scale, col, gap=None):
    if gap is None:
        gap = scale
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT[' '])
        for r, row in enumerate(glyph):
            for c, bit in enumerate(row):
                if bit == '1':
                    fill_rect(cx + c * scale, y + r * scale,
                              cx + (c + 1) * scale, y + (r + 1) * scale, col)
        cx += 5 * scale + gap


# --- title: place name, large and legible, centred at the top ---
NAME = "LUMARELLE"
SCALE = 15
tw = text_width(NAME, SCALE, SCALE)
draw_text(NAME, (W - tw) // 2, 64, SCALE, CREAM)
# warm underline rule under the name
fill_rect((W - tw) // 2, 64 + 7 * SCALE + 18, (W + tw) // 2, 64 + 7 * SCALE + 22, AMBER)
# subtitle: one line that says what the place is
SUB = "THE LAGOON OF DRIFTING LIGHT"
SS = 5
sw = text_width(SUB, SS, SS)
draw_text(SUB, (W - sw) // 2, 64 + 7 * SCALE + 40, SS, _mix(CREAM, PEACH, 0.35))

# --- PNG encoder (zlib + struct, filter 0) ---
def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw.extend(px[y * W * 3:(y + 1) * W * 3])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def main():
    out_dir = os.environ.get("OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    write_png(os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
