"""Render the catalogue photo: a chrome toaster toasting a sock.

SOCK-O-MATIC 3000 — a 1-slice sock toaster, shot as a studio product photo.
Drawn at 2x (2048) and downscaled to 1024 for anti-aliasing. Fully
deterministic: fixed seed, no timestamps, no network.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 2  # supersample factor
W = 1024 * S
H = 1024 * S

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
F_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
F_REG = os.path.join(FONT_DIR, "DejaVuSans.ttf")


def font(path, size):
    return ImageFont.truetype(path, size)


def vgrad(size, stops):
    """Vertical gradient. stops: list of (pos 0..1, (r,g,b))."""
    w, h = size
    ys = np.linspace(0.0, 1.0, h)
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for ch in range(3):
        xs = [s[0] for s in stops]
        vs = [s[1][ch] for s in stops]
        arr[:, :, ch] = np.interp(ys, xs, vs)[:, None]
    return Image.fromarray(arr, "RGB")


def hgrad(size, stops):
    w, h = size
    xs = np.linspace(0.0, 1.0, w)
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for ch in range(3):
        px = [s[0] for s in stops]
        vs = [s[1][ch] for s in stops]
        arr[:, :, ch] = np.interp(xs, px, vs)[None, :]
    return Image.fromarray(arr, "RGB")


def soft_shadow(img, box, blur, alpha):
    """Draw a soft elliptical shadow on img. box=(x0,y0,x1,y1)."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse(box, fill=(0, 0, 0, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(layer)


def rounded(draw, box, radius, **kw):
    draw.rounded_rectangle(box, radius=radius, **kw)


def draw_sock_body(d, x0, y0, x1, y1, base=(243, 234, 216)):
    """Sock silhouette: tube with cuff at top and heel bulge on the left."""
    d.rounded_rectangle([x0, y0, x1, y1], radius=42, fill=base)
    # heel bulge, left side, mid-body
    d.ellipse([x0 - 26, y0 + 300, x0 + 90, y0 + 470], fill=base)


def argyle_clip(sock_layer, mask, x0, y0, x1, y1, step=150):
    """Argyle diamonds clipped to the sock mask."""
    pat = Image.new("RGBA", sock_layer.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(pat)
    navy = (46, 74, 107, 255)
    red = (176, 58, 46, 255)
    for row in range(-2, 10):
        for col in range(-2, 8):
            cx = x0 + 60 + col * step
            cy = y0 + 560 + row * step
            if (row + col) % 2 == 0:
                colr = navy
            else:
                colr = red
            r = step // 2 - 13
            pd.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r),
                        (cx - r, cy)], fill=colr)
    # thin diagonal cross lines through diamonds
    for row in range(-2, 8):
        for col in range(-2, 6):
            cx = x0 + 60 + col * step
            cy = y0 + 560 + row * step
            pd.line([(cx - 62, cy - 62), (cx + 62, cy + 62)],
                    fill=(255, 255, 255, 70), width=5)
            pd.line([(cx - 62, cy + 62), (cx + 62, cy - 62)],
                    fill=(255, 255, 255, 70), width=5)
    sock_layer.paste(Image.composite(pat, Image.new("RGBA", sock_layer.size, (0, 0, 0, 0)), mask), (0, 0), mask)


def render():
    rng = np.random.RandomState(42)
    img = vgrad((W, H), [(0.0, (248, 246, 242)), (0.55, (238, 235, 229)),
                         (1.0, (226, 222, 215))]).convert("RGBA")

    # soft radial glow behind the product
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([340, 240, 1700, 1680], fill=(255, 253, 248, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(260))
    img.alpha_composite(glow)

    # floor: faint horizon + contact shadows
    d = ImageDraw.Draw(img)
    d.line([(0, 1600), (W, 1600)], fill=(200, 196, 188, 255), width=4)
    soft_shadow(img, [470, 1520, 1620, 1660], 42, 60)
    soft_shadow(img, [1600, 1540, 2030, 1640], 30, 46)

    # ---------- cord: from toaster back, snaking off the right edge ----------
    cord = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cord)
    pts = []
    for t in np.linspace(0, 1, 60):
        x = 1480 + 460 * t
        y = 1520 + 60 * math.sin(t * 2.4) + 170 * t
        pts.append((x, y))
    cd.line(pts, fill=(38, 38, 40, 255), width=16, joint="curve")
    cd.line(pts, fill=(70, 70, 72, 255), width=6, joint="curve")
    img.alpha_composite(cord)

    # ---------- toaster body ----------
    body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    chrome = vgrad((980, 500), [(0.0, (244, 245, 247)), (0.22, (216, 219, 224)),
                                (0.42, (168, 173, 180)), (0.55, (198, 202, 208)),
                                (0.78, (232, 234, 236)), (1.0, (196, 199, 204))])
    # brushed-metal grain
    grain = rng.normal(0, 5, (500, 980, 1)).repeat(3, axis=2)
    carr = np.asarray(chrome).astype(np.int16) + grain.astype(np.int16)
    chrome = Image.fromarray(np.clip(carr, 0, 255).astype(np.uint8), "RGB")
    mask = Image.new("L", (980, 500), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, 980, 500], radius=80, fill=255)
    body.paste(chrome, (520, 1060), mask)
    # specular highlight strip on the left third
    hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.rounded_rectangle([600, 1080, 760, 1540], radius=60,
                         fill=(255, 255, 255, 90))
    hl = hl.filter(ImageFilter.GaussianBlur(26))
    body.alpha_composite(hl)
    # bottom edge shade
    bd = ImageDraw.Draw(body)
    bd.rounded_rectangle([520, 1060, 1500, 1560], radius=80,
                         outline=(120, 124, 130, 255), width=4)
    bd.line([(540, 1540), (1480, 1540)], fill=(140, 144, 150, 160), width=6)
    img.alpha_composite(body)

    # ---------- top plate + slots ----------
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([560, 1000, 1460, 1095], radius=34, fill=(38, 40, 42, 255))
    d.rounded_rectangle([560, 1000, 1460, 1095], radius=34,
                        outline=(90, 92, 96, 255), width=3)
    d.rounded_rectangle([700, 1018, 990, 1078], radius=22, fill=(8, 8, 10, 255))
    d.rounded_rectangle([1060, 1018, 1350, 1078], radius=22, fill=(8, 8, 10, 255))
    # slot rims
    d.rounded_rectangle([700, 1018, 990, 1078], radius=22,
                        outline=(120, 122, 126, 255), width=4)
    d.rounded_rectangle([1060, 1018, 1350, 1078], radius=22,
                        outline=(120, 122, 126, 255), width=4)

    # ---------- the sock, rising from the left slot ----------
    sock = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sock)
    x0, x1 = 752, 948
    y_top, y_bot = 372, 1030
    draw_sock_body(sd, x0, y_top, x1, y_bot)
    # mask of the silhouette for the pattern
    smask = Image.new("L", (W, H), 0)
    smd = ImageDraw.Draw(smask)
    draw_sock_body(smd, x0, y_top, x1, y_bot, base=255)
    argyle_clip(sock, smask, x0, y_top, x1, y_bot)
    sd = ImageDraw.Draw(sock)
    # heel patch (red), smaller and tucked to the sock's left edge
    sd.ellipse([x0 - 14, y_top + 330, x0 + 66, y_top + 452],
               fill=(176, 58, 46, 255))
    sd.ellipse([x0 - 14, y_top + 330, x0 + 66, y_top + 452],
               outline=(140, 40, 30, 255), width=4)
    # cuff: ribbed band at the top
    sd.rounded_rectangle([x0, y_top, x1, y_top + 128], radius=40,
                         fill=(238, 228, 208, 255))
    for i in range(9):
        xx = x0 + 14 + i * 22
        sd.line([(xx, y_top + 8), (xx, y_top + 120)],
                fill=(205, 192, 168, 255), width=6)
    # toasted top edge: browned gradient, darkest at the very top
    toast = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tg = vgrad((x1 - x0, 90), [(0.0, (122, 74, 32, 235)), (1.0, (150, 100, 55, 0))])
    tmask = Image.new("L", (x1 - x0, 90), 0)
    td = ImageDraw.Draw(tmask)
    td.rounded_rectangle([0, 0, x1 - x0, 90], radius=40, fill=255)
    td.rectangle([0, 40, x1 - x0, 90], fill=255)
    toast.paste(tg, (x0, y_top), tmask)
    sock.alpha_composite(toast)
    # outline for a sewn look
    sd = ImageDraw.Draw(sock)
    sd.rounded_rectangle([x0, y_top, x1, y_bot], radius=42,
                         outline=(190, 175, 150, 255), width=4)
    # tilt the sock a touch and paste
    sock = sock.rotate(4, center=(x0 + 100, y_bot), resample=Image.BICUBIC)
    img.alpha_composite(sock)

    # ---------- steam: one gentle wisp above the sock ----------
    steam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    std = ImageDraw.Draw(steam)
    pts = []
    for t in np.linspace(0, 1, 40):
        y = 372 - 200 * t
        x = 850 + 18 * math.sin(t * 3.0)
        pts.append((x, y))
    std.line(pts, fill=(255, 255, 255, 70), width=11, joint="curve")
    steam = steam.filter(ImageFilter.GaussianBlur(12))
    img.alpha_composite(steam)

    # ---------- lever (right side, pushed down) ----------
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([1492, 1230, 1568, 1270], radius=16, fill=(200, 203, 208, 255))
    d.rounded_rectangle([1492, 1230, 1568, 1270], radius=16,
                        outline=(130, 134, 140, 255), width=3)
    d.ellipse([1536, 1218, 1600, 1282], fill=(30, 30, 32, 255))
    d.ellipse([1550, 1232, 1586, 1268], fill=(80, 82, 86, 255))

    # ---------- dial ----------
    cx, cy, r = 1190, 1330, 130
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10],
              fill=(214, 217, 221, 255), outline=(150, 154, 160, 255), width=4)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(43, 46, 49, 255))
    labels = [("DAMP", -140), ("WARM", -70), ("CRISP", 10), ("CHARRED", 80)]
    f_lab = font(F_REG, 24)
    for text, ang in labels:
        a = math.radians(ang - 90)
        lx = cx + int(0.55 * r * math.cos(a))
        ly = cy + int(0.55 * r * math.sin(a))
        bb = d.textbbox((0, 0), text, font=f_lab)
        d.text((lx - (bb[2] - bb[0]) // 2, ly - (bb[3] - bb[1]) // 2),
               text, font=f_lab, fill=(220, 222, 225, 255))
    # ticks
    for ang in range(-140, 141, 20):
        a = math.radians(ang - 90)
        x1 = cx + int(0.88 * r * math.cos(a))
        y1 = cy + int(0.88 * r * math.sin(a))
        x2 = cx + int(0.97 * r * math.cos(a))
        y2 = cy + int(0.97 * r * math.sin(a))
        d.line([(x1, y1), (x2, y2)], fill=(200, 202, 206, 255), width=5)
    # pointer at CRISP (10 deg)
    a = math.radians(10 - 90)
    px = cx + int(0.62 * r * math.cos(a))
    py = cy + int(0.62 * r * math.sin(a))
    d.line([(cx, cy), (px, py)], fill=(240, 80, 60, 255), width=10)
    d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=(200, 203, 208, 255))

    # ---------- front text (product text only) ----------
    f_brand = font(F_BOLD, 62)
    f_small = font(F_REG, 30)
    f_tiny = font(F_REG, 26)
    d.text((600, 1130), "SOCK-O-MATIC", font=f_brand, fill=(52, 54, 58, 255))
    d.text((600, 1200), "3000", font=f_small, fill=(90, 92, 96, 255))
    d.text((600, 1470), "220V · 800W · 1-SLICE", font=f_tiny, fill=(110, 112, 116, 255))
    d.text((600, 1096), "TOASTY-FEET™", font=f_tiny, fill=(120, 122, 126, 255))

    # ---------- rubber feet ----------
    d.rounded_rectangle([640, 1556, 730, 1592], radius=14, fill=(30, 30, 32, 255))
    d.rounded_rectangle([1290, 1556, 1380, 1592], radius=14, fill=(30, 30, 32, 255))

    # ---------- accessory: one folded sock, lying flat at the right ----------
    acc = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ad = ImageDraw.Draw(acc)
    ax0, ay0, ax1, ay1 = 1600, 1410, 2010, 1590
    ad.rounded_rectangle([ax0, ay0, ax1, ay1], radius=48, fill=(243, 234, 216, 255))
    # argyle on the folded sock
    amask = Image.new("L", (W, H), 0)
    amd = ImageDraw.Draw(amask)
    amd.rounded_rectangle([ax0, ay0, ax1, ay1], radius=48, fill=255)
    argyle_clip(acc, amask, ax0, ay0 - 480, ax1, ay1, step=110)
    ad = ImageDraw.Draw(acc)
    # cuff band at the right end
    ad.rounded_rectangle([ax1 - 120, ay0, ax1, ay1], radius=48,
                         fill=(176, 58, 46, 255))
    ad.rectangle([ax1 - 120, ay0 + 48, ax1 - 60, ay1 - 48],
                 fill=(176, 58, 46, 255))
    for i in range(4):
        xx = ax1 - 108 + i * 22
        ad.line([(xx, ay0 + 10), (xx, ay1 - 10)], fill=(140, 40, 30, 255), width=5)
    # fold seam line
    ad.line([(ax0 + 30, ay0 + 70), (ax1 - 150, ay0 + 70)],
            fill=(205, 192, 168, 255), width=5)
    ad.rounded_rectangle([ax0, ay0, ax1, ay1], radius=48,
                         outline=(190, 175, 150, 255), width=4)
    acc = acc.rotate(-3, center=((ax0 + ax1) // 2, (ay0 + ay1) // 2),
                     resample=Image.BICUBIC)
    img.alpha_composite(acc)

    # final downscale to 1024
    out = img.convert("RGB").resize((1024, 1024), Image.LANCZOS)
    return out


if __name__ == "__main__":
    import sys
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    im = render()
    im.save(os.path.join(out_dir, "entry.png"), format="PNG")
    print("saved", os.path.join(out_dir, "entry.png"))
