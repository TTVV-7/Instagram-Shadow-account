"""Render the a-day-in-3D cover slide (1080x1350) with a hero photo, matching the Figma component."""
import sys
from PIL import Image, ImageDraw, ImageFont

FONTS, hero_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
HEADLINE = sys.argv[4] if len(sys.argv) > 4 else "AI designs parts your printer can print"
KICKER = "AI × 3D printing"
ISSUE, DATE = "ISSUE #01", "Oct 26, 2026"

W, H, SAFE = 1080, 1350, 80
BG, ACCENT, TEXT, MUTED, DIVIDER, ON_ACCENT = "#0B0D10", "#C6FF3D", "#F2F2EE", "#B4BAC0", "#2A2E35", "#0B0D10"


def font(name, size, axes):
    f = ImageFont.truetype(f"{FONTS}/{name}", size)
    f.set_variation_by_axes(axes)
    return f


SG = lambda s: font("SpaceGrotesk%5Bwght%5D.ttf", s, [700])
JM = lambda s, w=500: font("JetBrainsMono%5Bwght%5D.ttf", s, [w])


def text_w(f, t, track):
    return sum(f.getlength(c) for c in t) + track * (len(t) - 1)


def draw_t(d, x, y, t, f, fill, track=0.0):
    for c in t:
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + track
    return x


def wrap(f, t, width, track):
    lines, cur = [], ""
    for word in t.split():
        trial = (cur + " " + word).strip()
        if text_w(f, trial, track) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    return lines + [cur]


head_f, head_track, head_lh = SG(128), -128 * 0.03, round(128 * 0.98)
label_f, label_track, label_lh = JM(34), 34 * 0.04, round(34 * 1.2)
lines = wrap(head_f, HEADLINE, W - 2 * SAFE, head_track)

# Content block height (mirrors the Figma auto layout: top 48, gap 32, bottom 80)
content_h = 48 + label_lh + 32 + head_lh * len(lines) + 32 + 2 + 32 + label_lh + SAFE
hero_h = H - content_h

img = Image.new("RGB", (W, H), BG)

# Hero photo: scale to cover, crop centred slightly low (subject usually sits mid-frame)
photo = Image.open(hero_path).convert("RGB")
scale = max(W / photo.width, hero_h / photo.height)
photo = photo.resize((round(photo.width * scale), round(photo.height * scale)), Image.LANCZOS)
top = min(max(0, int((photo.height - hero_h) * 0.55)), photo.height - hero_h)
left = (photo.width - W) // 2
img.paste(photo.crop((left, top, left + W, top + hero_h)), (0, 0))

# Gradient overlay: 70% at top -> clear at 30% -> clear at 60% -> solid bg at bottom
bg_rgb = (11, 13, 16)
overlay = Image.new("RGBA", (W, hero_h))
od = ImageDraw.Draw(overlay)
for y in range(hero_h):
    p = y / hero_h
    a = 0.7 * (1 - p / 0.3) if p < 0.3 else 0 if p < 0.6 else (p - 0.6) / 0.4
    od.line([(0, y), (W, y)], fill=bg_rgb + (round(255 * a),))
img.paste(overlay, (0, 0), overlay)

d = ImageDraw.Draw(img)

# Top bar: wordmark + issue pill
wm = SG(40)
x = draw_t(d, SAFE, SAFE, "a day in ", wm, TEXT, -0.8)
draw_t(d, x, SAFE, "3D", wm, ACCENT, -0.8)
pw = text_w(label_f, ISSUE, label_track) + 52
ph = label_lh + 28
px = W - SAFE - pw
d.rounded_rectangle([px, SAFE - 10, px + pw, SAFE - 10 + ph], radius=ph / 2, fill=ACCENT)
draw_t(d, px + 26, SAFE - 10 + 14, ISSUE, label_f, ON_ACCENT, label_track)

# Content
y = hero_h + 48
d.rectangle([SAFE, y + 10, SAFE + 20, y + 30], fill=ACCENT)
draw_t(d, SAFE + 36, y, KICKER.upper(), label_f, ACCENT, label_track)
y += label_lh + 32
for ln in lines:
    draw_t(d, SAFE, y, ln, head_f, TEXT, head_track)
    y += head_lh
y += 32
d.rectangle([SAFE, y, W - SAFE, y + 1], fill=DIVIDER)
y += 2 + 32
draw_t(d, SAFE, y, DATE.upper(), label_f, MUTED, label_track)
sw = "SWIPE →"
draw_t(d, W - SAFE - text_w(label_f, sw, label_track), y, sw, label_f, ACCENT, label_track)

img.save(out_path)
print(out_path, len(lines), "lines; hero", hero_h)
