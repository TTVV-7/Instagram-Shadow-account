"""Render a full "a day in 3D" carousel (1080x1350 slides) from a JSON spec, matching the Figma components.

Usage: python3 tools/render_deck.py <fonts-dir> <deck.json> <out-dir>
The cover slide is rendered by tools/render_cover.py; this script renders story, quick-hits and cta slides.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

FONTS, spec_path, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
spec = json.load(open(spec_path))
base = os.path.dirname(os.path.abspath(spec_path))

W, H, SAFE = 1080, 1350, 80
BG, SURFACE, PLACEHOLDER = "#0B0D10", "#1A1D22", "#2A2E35"
ACCENT, TEXT, MUTED, DIVIDER, ON_ACCENT = "#C6FF3D", "#F2F2EE", "#B4BAC0", "#2A2E35", "#0B0D10"


def font(name, size, axes):
    f = ImageFont.truetype(f"{FONTS}/{name}", size)
    f.set_variation_by_axes(axes)
    return f


SG = lambda s: font("SpaceGrotesk%5Bwght%5D.ttf", s, [700])
JM = lambda s, w=500: font("JetBrainsMono%5Bwght%5D.ttf", s, [w])
INTER = lambda s, w=400: font("Inter%5Bopsz,wght%5D.ttf", s, [32, w])

# Text styles: (font, letter-spacing px, line height px, uppercase)
STYLE = {
    "headline": (SG(84), -84 * 0.02, round(84 * 1.04), False),
    "prompt": (SG(64), -64 * 0.015, round(64 * 1.08), False),
    "body": (INTER(40), 0, round(40 * 1.38), False),
    "body-medium": (INTER(40, 500), 0, round(40 * 1.38), False),
    "list": (INTER(44, 500), -44 * 0.005, round(44 * 1.3), False),
    "label": (JM(34), 34 * 0.04, round(34 * 1.2), True),
    "wordmark": (SG(40), -0.8, 40, False),
    "mark": (SG(80), -2.4, 80, False),
}


def width(style, t):
    f, track, _, upper = STYLE[style]
    t = t.upper() if upper else t
    return sum(f.getlength(c) for c in t) + track * max(0, len(t) - 1)


def wrap(style, t, max_w):
    lines, cur = [], ""
    for word in t.split():
        trial = (cur + " " + word).strip()
        if width(style, trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    return lines + [cur]


def draw_line(d, x, y, t, style, fill):
    f, track, lh, upper = STYLE[style]
    t = t.upper() if upper else t
    # Center glyphs vertically inside the line box the way Figma does
    asc, desc = f.getmetrics()
    y += (lh - (asc + desc)) / 2
    for c in t:
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + track


def draw_block(d, x, y, t, style, fill, max_w, align="left"):
    lh = STYLE[style][2]
    lines = wrap(style, t, max_w)
    for ln in lines:
        lx = x + (max_w - width(style, ln)) / 2 if align == "center" else x
        draw_line(d, lx, y, ln, style, fill)
        y += lh
    return y


def block_h(style, t, max_w):
    return STYLE[style][2] * len(wrap(style, t, max_w))


def paste_cover(img, path, box, radius, crop=0.5):
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    photo = Image.open(os.path.join(base, path)).convert("RGB")
    s = max(bw / photo.width, bh / photo.height)
    photo = photo.resize((round(photo.width * s), round(photo.height * s)), Image.LANCZOS)
    top = min(max(0, int((photo.height - bh) * crop)), photo.height - bh)
    left = (photo.width - bw) // 2
    tile = photo.crop((left, top, left + bw, top + bh))
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, bw - 1, bh - 1], radius=radius, fill=255)
    img.paste(tile, (x0, y0), mask)


def top_bar(d, left_text, slide_no, wordmark=False):
    lh = STYLE["label"][2]
    if wordmark:
        draw_line(d, SAFE, SAFE - 3, "a day in ", "wordmark", TEXT)
        draw_line(d, SAFE + width("wordmark", "a day in "), SAFE - 3, "3D", "wordmark", ACCENT)
    else:
        draw_line(d, SAFE, SAFE, left_text, "label", ACCENT)
    draw_line(d, W - SAFE - width("label", slide_no), SAFE, slide_no, "label", MUTED)
    return SAFE + lh


def footer(d, left, right):
    y = H - SAFE - STYLE["label"][2]
    draw_line(d, SAFE, y, left, "label", MUTED)
    draw_line(d, W - SAFE - width("label", right), y, right, "label", ACCENT)


CW = W - 2 * SAFE  # content width


def story(s):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    gap = 32
    y = top_bar(d, s["kicker"], s["slide"]) + gap
    # Take card geometry
    take_w = CW - 32 - 40 - 8 - 28
    take_h = 32 + STYLE["label"][2] + 10 + block_h("body-medium", s["take"], take_w) + 32
    text_h = block_h("headline", s["headline"], CW) + gap + block_h("body", s["summary"], CW) + gap + take_h
    img_h = H - SAFE - y - gap - text_h
    paste_cover(img, s["image"], (SAFE, y, W - SAFE, y + img_h), 32, s.get("crop", 0.5))
    y += img_h + gap
    y = draw_block(d, SAFE, y, s["headline"], "headline", TEXT, CW) + gap
    y = draw_block(d, SAFE, y, s["summary"], "body", MUTED, CW) + gap
    d.rounded_rectangle([SAFE, y, W - SAFE, y + take_h], radius=32, fill=SURFACE)
    d.rounded_rectangle([SAFE + 32, y + 32, SAFE + 40, y + take_h - 32], radius=4, fill=ACCENT)
    tx = SAFE + 32 + 8 + 28
    draw_line(d, tx, y + 32, "My take:", "label", ACCENT)
    draw_block(d, tx, y + 32 + STYLE["label"][2] + 10, s["take"], "body-medium", TEXT, take_w)
    return img


def quick_hits(s):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    y = top_bar(d, s.get("kicker", "Quick hits"), s["slide"]) + 48
    y = draw_block(d, SAFE, y, s["headline"], "headline", TEXT, CW) + 48
    text_x = SAFE + 80 + 32
    text_w = CW - 80 - 32
    d.rectangle([SAFE, y, W - SAFE, y + 1], fill=DIVIDER)
    for i, hit in enumerate(s["hits"]):
        th = block_h("list", hit, text_w)
        row_h = 48 + max(80, th) + 48
        cy = y + row_h / 2
        d.rounded_rectangle([SAFE, cy - 40, SAFE + 80, cy + 40], radius=20, fill=ACCENT)
        num = f"{i + 1:02d}"
        draw_line(d, SAFE + 40 - width("label", num) / 2, cy - STYLE["label"][2] / 2, num, "label", ON_ACCENT)
        draw_block(d, text_x, cy - th / 2, hit, "list", TEXT, text_w)
        y += row_h
        d.rectangle([SAFE, y - 2, W - SAFE, y - 1], fill=DIVIDER)
    footer(d, s["handle"], "Swipe →")
    return img


def cta(s):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    top = top_bar(d, "", s["slide"], wordmark=True)
    foot_h = STYLE["label"][2]
    card_w = CW - 2 * 96
    card_h = 48 + STYLE["label"][2] + 16 + block_h("prompt", s["prompt"], card_w) + 48
    stack_h = 176 + 48 + block_h("headline", s["headline"], CW) + 48 + STYLE["body-medium"][2] + 48 + card_h
    y = top + (H - SAFE - foot_h - top - stack_h) / 2
    d.rounded_rectangle([W / 2 - 88, y, W / 2 + 88, y + 176], radius=44, fill=ACCENT)
    draw_line(d, W / 2 - width("mark", "3D") / 2, y + 88 - 40, "3D", "mark", ON_ACCENT)
    y += 176 + 48
    y = draw_block(d, SAFE, y, s["headline"], "headline", TEXT, CW, "center") + 48
    draw_line(d, W / 2 - width("body-medium", s["handle"]) / 2, y, s["handle"], "body-medium", ACCENT)
    y += STYLE["body-medium"][2] + 48
    d.rounded_rectangle([SAFE, y, W - SAFE, y + card_h], radius=32, fill=SURFACE)
    lab = "Comment below ↓"
    draw_line(d, W / 2 - width("label", lab) / 2, y + 48, lab, "label", ACCENT)
    draw_block(d, SAFE + 96, y + 48 + STYLE["label"][2] + 16, s["prompt"], "prompt", TEXT, card_w, "center")
    fh = s["footer"]
    draw_line(d, W / 2 - width("label", fh) / 2, H - SAFE - foot_h, fh, "label", ACCENT)
    return img


def text(s):
    """Text-only slide: headline, short paragraphs, and an optional take card pinned above the footer."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    y = top_bar(d, s["kicker"], s["slide"]) + 48
    y = draw_block(d, SAFE, y, s["headline"], "headline", TEXT, CW) + 40
    for para in s.get("body", []):
        y = draw_block(d, SAFE, y, para, "body", TEXT, CW) + 28
    if s.get("take"):
        take_w = CW - 32 - 40 - 8 - 28
        take_h = 32 + STYLE["label"][2] + 10 + block_h("body-medium", s["take"], take_w) + 32
        ty = H - SAFE - STYLE["label"][2] - 48 - take_h
        d.rounded_rectangle([SAFE, ty, W - SAFE, ty + take_h], radius=32, fill=SURFACE)
        d.rounded_rectangle([SAFE + 32, ty + 32, SAFE + 40, ty + take_h - 32], radius=4, fill=ACCENT)
        tx = SAFE + 32 + 8 + 28
        draw_line(d, tx, ty + 32, "My take:", "label", ACCENT)
        draw_block(d, tx, ty + 32 + STYLE["label"][2] + 10, s["take"], "body-medium", TEXT, take_w)
    footer(d, s.get("handle", "@printyours.ca"), "Swipe →")
    return img


RENDER = {"story": story, "quick-hits": quick_hits, "text": text, "cta": cta}
os.makedirs(out_dir, exist_ok=True)
for i, s in enumerate(spec["slides"], start=1):
    if s["type"] in RENDER:
        out = os.path.join(out_dir, f"slide-{i}.png")
        RENDER[s["type"]](s).save(out)
        print(out)
