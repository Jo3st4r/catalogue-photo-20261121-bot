"""SOCK-O-MATIC 3000 — studio catalogue photo of a chrome 1-slice sock toaster.

Drawn from scratch with PIL only. Deterministic: fixed geometry plus a
seeded RNG for brushed grain and toast blotches. No network, no timestamps.
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1024
RNG = random.Random(20261121)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def _font(name, size):
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    except Exception:
        return ImageFont.load_default()


def F_BOLD(s):
    return _font("DejaVuSans-Bold.ttf", s)


def F_REG(s):
    return _font("DejaVuSans.ttf", s)


def _smooth(points, per_seg=10):
    """Catmull-Rom spline through points; returns a denser polyline."""
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(len(pts) - 3):
        p0, p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2], pts[i + 3]
        for j in range(per_seg):
            t = j / per_seg
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(points[-1])
    return out


def _vgrad(size, stops):
    """Vertical gradient image. stops: list of (pos 0..1, (r,g,b))."""
    w, h = size
    img = Image.new("RGB", (1, h))
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                f = 0 if p1 == p0 else (t - p0) / (p1 - p0)
                px[0, y] = tuple(int(c0[k] + (c1[k] - c0[k]) * f) for k in range(3))
                break
        else:
            px[0, y] = stops[-1][1]
    return img.resize((w, h))


def _hgrad(size, stops):
    """Horizontal gradient image."""
    w, h = size
    img = Image.new("RGB", (w, 1))
    px = img.load()
    for x in range(w):
        t = x / max(1, w - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                f = 0 if p1 == p0 else (t - p0) / (p1 - p0)
                px[x, 0] = tuple(int(c0[k] + (c1[k] - c0[k]) * f) for k in range(3))
                break
        else:
            px[x, 0] = stops[-1][1]
    return img.resize((w, h))


def _soft_shadow(base, box, blur, alpha):
    """Blurred black ellipse shadow pasted onto base (RGBA layer)."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse(box, fill=(0, 0, 0, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(layer)


def _text_center(d, cx, y, s, font, fill, shadow=None):
    bbox = d.textbbox((0, 0), s, font=font)
    w = bbox[2] - bbox[0]
    if shadow is not None:
        d.text((cx - w / 2 + 1, y + 1), s, font=font, fill=shadow)
    d.text((cx - w / 2, y), s, font=font, fill=fill)
    return w


def _chrome_body(size):
    """Brushed chrome panel with vertical specular bands (RGB)."""
    w, h = size
    stops = [
        (0.00, (88, 90, 96)),
        (0.07, (208, 210, 214)),
        (0.16, (148, 150, 156)),
        (0.30, (236, 237, 239)),
        (0.38, (168, 170, 176)),
        (0.45, (246, 247, 249)),
        (0.53, (182, 184, 189)),
        (0.70, (138, 140, 146)),
        (0.88, (206, 207, 211)),
        (1.00, (102, 104, 110)),
    ]
    img = _hgrad((w, h), stops)
    # Vertical falloff: slightly darker toward the bottom.
    shade = _vgrad((w, h), [(0.0, (255, 255, 255)), (1.0, (205, 205, 205))])
    px = img.load()
    sh = shade.load()
    for y in range(h):
        f = sh[0, y][0] / 255.0
        for x in range(w):
            r, g, b = px[x, y]
            px[x, y] = (int(r * f), int(g * f), int(b * f))
    # Brushed grain: faint horizontal streaks, seeded.
    grain = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grain)
    for _ in range(520):
        y = RNG.randrange(h)
        x0 = RNG.randrange(0, w - 40)
        x1 = x0 + RNG.randrange(20, 160)
        v = RNG.choice([(255, 255, 255), (0, 0, 0)])
        gd.line([(x0, y), (x1, y)], fill=v + (RNG.randrange(6, 20),), width=1)
    img = Image.alpha_composite(img.convert("RGBA"), grain)
    return img.convert("RGB")


def _argyle_layer(box, base, dia1, dia2, spacing=46):
    """Argyle diamond pattern clipped to a rounded box; returns RGBA layer."""
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle(box, radius=26, fill=base + (255,))
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle(box, radius=26, fill=255)
    pat = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pat)
    r = 25
    row = 0
    y = y0 - spacing
    while y < y1 + spacing:
        x = x0 - spacing + (spacing // 2 if row % 2 else 0)
        col = 0
        while x < x1 + spacing:
            c = dia1 if (row + col) % 2 == 0 else dia2
            pd.polygon(
                [(x, y - r), (x + r, y), (x, y + r), (x - r, y)], fill=c + (255,)
            )
            x += spacing
            col += 1
        y += spacing // 2 + 8
        row += 1
    pat.putalpha(Image.composite(pat.split()[3], Image.new("L", (W, H), 0), mask))
    layer.alpha_composite(pat)
    return layer


def _sock_mask(points, width):
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.line(points, fill=255, width=width, joint="curve")
    return mask


def render():
    img = Image.new("RGB", (W, H))
    # Warm-gray seamless backdrop.
    bg = _vgrad((W, H), [(0.0, (198, 189, 178)), (0.55, (186, 177, 165)), (1.0, (166, 157, 144))])
    img.paste(bg, (0, 0))
    base = img.convert("RGBA")

    # Soft radial studio light, upper centre.
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((180, -260, 844, 620), fill=(255, 250, 240, 26))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))

    # Floor shadows.
    _soft_shadow(base, (265, 792, 685, 838), 9, 95)   # toaster
    _soft_shadow(base, (688, 788, 962, 830), 8, 80)   # accessory sock

    # ---- power cord (behind the toaster body) ----
    cord = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cord)
    pts = _smooth([(640, 768), (716, 826), (700, 884), (798, 922), (902, 904), (1018, 962)])
    cd.line(pts, fill=(28, 28, 32, 255), width=11, joint="curve")
    cd.line([(x, y - 3) for x, y in pts], fill=(74, 74, 80, 255), width=3, joint="curve")
    base.alpha_composite(cord)

    # ---- accessory: one folded argyle sock, flat on the right ----
    acc = _argyle_layer(
        (692, 726, 956, 798),
        (239, 230, 210), (176, 58, 46), (91, 107, 122),
    )
    base.alpha_composite(acc)
    ad = ImageDraw.Draw(base)
    # Red cuff band at the right end of the folded sock.
    ad.rounded_rectangle((892, 726, 956, 798), radius=24, fill=(176, 58, 46, 255))
    ad.line([(908, 730), (908, 794)], fill=(120, 30, 24, 255), width=3)
    ad.line([(928, 730), (928, 794)], fill=(120, 30, 24, 255), width=3)
    # Fold crease lines.
    ad.line([(742, 730), (742, 794)], fill=(196, 182, 158, 255), width=3)
    ad.line([(812, 730), (812, 794)], fill=(196, 182, 158, 255), width=3)

    # ---- toaster chrome body ----
    body_x0, body_y0, body_x1, body_y1 = 300, 400, 650, 800
    chrome = _chrome_body((body_x1 - body_x0, body_y1 - body_y0))
    body_mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(body_mask)
    md.rounded_rectangle((body_x0, body_y0, body_x1, body_y1), radius=28, fill=255)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.paste(chrome, (body_x0, body_y0))
    layer.putalpha(Image.composite(layer.split()[3], Image.new("L", (W, H), 0), body_mask))
    base.alpha_composite(layer)
    d = ImageDraw.Draw(base)
    # Thin darker rim around the body.
    d.rounded_rectangle((body_x0, body_y0, body_x1, body_y1), radius=28,
                        outline=(70, 72, 78, 255), width=3)

    # ---- sock rising from the left slot (drawn before the top plate) ----
    sock_pts = [(386, 416), (373, 342), (379, 272), (393, 212), (399, 176)]
    sock_w = 104
    smask = _sock_mask(sock_pts, sock_w)
    sock = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sock)
    sd.line(sock_pts, fill=(239, 230, 210, 255), width=sock_w, joint="curve")
    # Argyle diamonds clipped to the sock.
    pat = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pat)
    r = 24
    row = 0
    y = 150
    while y < 430:
        x = 300 + (23 if row % 2 else 0)
        col = 0
        while x < 480:
            c = (176, 58, 46) if (row + col) % 2 == 0 else (91, 107, 122)
            pd.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], fill=c + (255,))
            x += 46
            col += 1
        y += 31
        row += 1
    pat.putalpha(Image.composite(pat.split()[3], Image.new("L", (W, H), 0), smask))
    sock.alpha_composite(pat)
    # Red heel patch on the sock's right side.
    heel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(heel)
    hd.ellipse((408, 282, 452, 348), fill=(176, 58, 46, 255))
    heel.putalpha(Image.composite(heel.split()[3], Image.new("L", (W, H), 0), smask))
    sock.alpha_composite(heel)
    # Toasted cuff: brown gradient over the top of the sock + toast blotches.
    toast = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(toast)
    for yy in range(150, 262):
        f = max(0.0, 1.0 - (yy - 150) / 112.0)
        td.line([(300, yy), (480, yy)], fill=(138, 90, 43, int(150 * f)))
    for _ in range(7):
        bx = RNG.randrange(350, 430)
        by = RNG.randrange(160, 240)
        td.ellipse((bx, by, bx + RNG.randrange(14, 30), by + RNG.randrange(8, 16)),
                   fill=(96, 58, 24, 90))
    toast.putalpha(Image.composite(toast.split()[3], Image.new("L", (W, H), 0), smask))
    sock.alpha_composite(toast)
    # Ribbed cuff lines across the top.
    rib = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rib)
    for yy in range(178, 224, 8):
        rd.line([(300, yy), (480, yy)], fill=(120, 84, 48, 110), width=2)
    rib.putalpha(Image.composite(rib.split()[3], Image.new("L", (W, H), 0), smask))
    sock.alpha_composite(rib)
    # Soft left-edge highlight for roundness.
    hi = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd2 = ImageDraw.Draw(hi)
    hd2.line([(352, 400), (344, 330), (349, 262), (362, 200)], fill=(255, 255, 255, 70),
             width=9, joint="curve")
    hi.putalpha(Image.composite(hi.split()[3], Image.new("L", (W, H), 0), smask))
    sock.alpha_composite(hi)
    base.alpha_composite(sock)

    # ---- black top plate + slots (covers the sock base) ----
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((300, 378, 650, 430), radius=14, fill=(24, 24, 26, 255))
    d.rounded_rectangle((300, 378, 650, 430), radius=14, outline=(90, 90, 94, 255), width=2)
    # Left slot (sock emerges from it) and right slot (empty).
    d.rounded_rectangle((338, 390, 434, 416), radius=8, fill=(8, 8, 10, 255))
    d.rounded_rectangle((338, 390, 434, 416), radius=8, outline=(70, 70, 74, 255), width=2)
    d.rounded_rectangle((500, 390, 596, 416), radius=8, fill=(8, 8, 10, 255))
    d.rounded_rectangle((500, 390, 596, 416), radius=8, outline=(70, 70, 74, 255), width=2)
    # Thin chrome rim where the sock meets the slot.
    d.arc((338, 392, 434, 424), start=180, end=360, fill=(200, 200, 204, 255), width=2)

    # ---- front-panel branding (product text only) ----
    d = ImageDraw.Draw(base)
    _text_center(d, 475, 462, "TOASTY-FEET\u2122", F_BOLD(26), (43, 43, 46),
                 shadow=(255, 255, 255))
    _text_center(d, 475, 500, "SOCK-O-MATIC", F_BOLD(40), (35, 35, 38),
                 shadow=(255, 255, 255))
    _text_center(d, 475, 552, "3000", F_BOLD(30), (43, 43, 46),
                 shadow=(255, 255, 255))
    _text_center(d, 475, 596, "220V \u00b7 800W \u00b7 1-SLICE", F_REG(19), (52, 52, 55),
                 shadow=(255, 255, 255))

    # ---- doneness dial ----
    cx, cy, rr = 415, 692, 50
    d.ellipse((cx - rr - 5, cy - rr - 5, cx + rr + 5, cy + rr + 5), fill=(40, 40, 44, 255))
    d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=(232, 230, 225, 255))
    d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(120, 120, 124, 255), width=2)
    labels = [("DAMP", 180), ("WARM", 225), ("CRISP", 315), ("CHARRED", 0)]
    for name, deg in labels:
        a = math.radians(deg)
        tx = cx + (rr + 40) * math.cos(a)
        ty = cy + (rr + 40) * math.sin(a)
        f = F_BOLD(13)
        bb = d.textbbox((0, 0), name, font=f)
        d.text((tx - (bb[2] - bb[0]) / 2, ty - (bb[3] - bb[1]) / 2 - 4), name,
               font=f, fill=(43, 43, 46))
    for deg in range(0, 360, 15):
        a = math.radians(deg)
        long_tick = deg % 45 == 0
        r0 = rr - (12 if long_tick else 7)
        d.line([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)),
                (cx + (rr - 3) * math.cos(a), cy + (rr - 3) * math.sin(a))],
               fill=(90, 90, 94, 255), width=2 if long_tick else 1)
    # Red pointer on CRISP (315 deg = upper right).
    a = math.radians(315)
    d.line([(cx, cy), (cx + (rr - 10) * math.cos(a), cy + (rr - 10) * math.sin(a))],
           fill=(176, 58, 46, 255), width=5)
    d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=(176, 58, 46, 255))

    # ---- side lever, pushed down ----
    d.rounded_rectangle((620, 545, 636, 660), radius=7, fill=(30, 30, 33, 255))
    d.rounded_rectangle((612, 640, 648, 670), radius=8, fill=(52, 52, 56, 255))
    d.rounded_rectangle((612, 640, 648, 670), radius=8, outline=(150, 150, 154, 255), width=2)

    # ---- rubber feet ----
    d.rounded_rectangle((322, 800, 372, 814), radius=5, fill=(28, 28, 30, 255))
    d.rounded_rectangle((578, 800, 628, 814), radius=5, fill=(28, 28, 30, 255))

    # ---- one faint steam wisp above the toasted cuff ----
    steam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(steam)
    for k, (sx, amp, ph) in enumerate([(384, 12, 0.0), (420, 9, 1.9)]):
        pts = []
        for i in range(41):
            t = i / 40.0
            y = 168 - t * 92
            x = sx + amp * math.sin(t * 5.2 + ph)
            pts.append((x, y))
        sd.line(pts, fill=(255, 255, 255, 46 - k * 12), width=7, joint="curve")
    base.alpha_composite(steam.filter(ImageFilter.GaussianBlur(3)))

    return base.convert("RGB")
