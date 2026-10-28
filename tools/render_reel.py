"""Turn a rendered carousel into a 9:16 Reel (1080x1920, 30fps MP4).

Scene 1 is a full-bleed hook: the hero photo with a slow zoom and a big headline.
The remaining scenes are the carousel's text slides, framed inside the Reel safe zone.

Usage: python3 tools/render_reel.py <fonts-dir> <hero.png> <deck-dir> <out.mp4> "<hook>" "<accent words>" <slide-durations...>
  slide-durations: seconds per carousel slide from slide-2 onward, e.g. 6 5 6 3
"""
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS, hero_path, deck_dir, out_path, HOOK, ACCENT_WORDS = sys.argv[1:7]
DURS = [float(x) for x in sys.argv[7:]]
HOOK_DUR, XFADE, FPS = 3.0, 0.35, 30
W, H = 1080, 1920
BG, ACCENT, TEXT, ON_ACCENT = (11, 13, 16), "#C6FF3D", "#F2F2EE", "#0B0D10"
# Instagram covers roughly the top 220px (header) and bottom 420px (caption, buttons) of a Reel
SAFE_TOP, SAFE_BOTTOM = 220, 420


def font(name, size, w):
    f = ImageFont.truetype(f"{FONTS}/{name}", size)
    f.set_variation_by_axes([w])
    return f


SG = font("SpaceGrotesk%5Bwght%5D.ttf", 112, 700)
WM = font("SpaceGrotesk%5Bwght%5D.ttf", 44, 700)
JM = font("JetBrainsMono%5Bwght%5D.ttf", 36, 600)


def tw(f, t, track=0):
    return sum(f.getlength(c) for c in t) + track * (len(t) - 1)


def draw_t(d, x, y, t, f, fill, track=0):
    for c in t:
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + track
    return x


# ---------- Scene 1: hook ----------
hero = Image.open(hero_path).convert("RGB")
scale = max(W / hero.width, H / hero.height) * 1.12  # headroom for the zoom
hero = hero.resize((round(hero.width * scale), round(hero.height * scale)), Image.LANCZOS)

overlay = Image.new("RGBA", (W, H))
od = ImageDraw.Draw(overlay)
for y in range(H):
    p = y / H
    a = 0.75 * (1 - p / 0.35) if p < 0.35 else 0 if p < 0.5 else min(1, (p - 0.5) / 0.3) * 0.92
    od.line([(0, y), (W, y)], fill=BG + (round(255 * a),))

# Headline text block (wrapped, accent words in lime), placed in the lower-middle safe area
track = -112 * 0.03
words, lines, cur = HOOK.split(), [], []
for w_ in words:
    trial = " ".join(cur + [w_])
    if tw(SG, trial, track) <= W - 160 or not cur:
        cur.append(w_)
    else:
        lines.append(cur)
        cur = [w_]
lines.append(cur)
accent = set(ACCENT_WORDS.split())
lh = 112
text_layer = Image.new("RGBA", (W, H))
td = ImageDraw.Draw(text_layer)
y0 = H - SAFE_BOTTOM - 40 - lh * len(lines)
# kicker pill above the headline
kick = "AI × 3D PRINTING"
kw = tw(JM, kick, 1.5) + 48
td.rounded_rectangle([80, y0 - 100, 80 + kw, y0 - 40], radius=30, fill=ACCENT)
draw_t(td, 104, y0 - 92, kick, JM, ON_ACCENT, 1.5)
for i, ln in enumerate(lines):
    x = 80
    for j, w_ in enumerate(ln):
        piece = w_ + (" " if j < len(ln) - 1 else "")
        x = draw_t(td, x, y0 + i * lh, piece, SG, ACCENT if w_.strip(".,!?’'") in accent else TEXT, track)
# wordmark at the top
x = draw_t(td, 80, SAFE_TOP - 20, "a day in ", WM, TEXT, -1)
draw_t(td, x, SAFE_TOP - 20, "3D", WM, ACCENT, -1)


def hook_frame(t):
    z = 1 + 0.06 * (t / HOOK_DUR)  # slow push-in
    k0 = min(hero.width / W, hero.height / H)  # largest 9:16 window that fits the photo
    cw, ch = W * k0 / z, H * k0 / z
    cx = hero.width / 2
    cy = min(max(hero.height * 0.42, ch / 2), hero.height - ch / 2)  # keep the crop inside the photo
    box = (max(0, cx - cw / 2), cy - ch / 2, min(hero.width, cx + cw / 2), cy + ch / 2)
    frame = hero.resize((W, H), Image.BILINEAR, box=box).convert("RGBA")
    frame.alpha_composite(overlay)
    # headline is fully visible from the first frame: it is the scroll-stopper and the thumbnail
    frame.alpha_composite(text_layer)
    return frame.convert("RGB")


# ---------- Text scenes ----------
def framed(i, last):
    slide = Image.open(f"{deck_dir}/slide-{i}.png").convert("RGB")
    if not last:  # drop the carousel footer ("SWIPE →" makes no sense in a Reel)
        ImageDraw.Draw(slide).rectangle([0, slide.height - 80 - 60, slide.width, slide.height], fill=BG)
    canvas = Image.new("RGB", (W, H), BG)
    usable = H - SAFE_TOP - SAFE_BOTTOM + 160  # slide footer may sit under the caption area
    s = min(1, usable / slide.height)
    slide = slide.resize((round(slide.width * s), round(slide.height * s)), Image.LANCZOS)
    canvas.paste(slide, ((W - slide.width) // 2, SAFE_TOP - 40))
    return canvas


scenes = [framed(i, i == 1 + len(DURS)) for i in range(2, 2 + len(DURS))]


def progress(frame, t, total):
    d = ImageDraw.Draw(frame)
    d.rectangle([0, 0, W, 8], fill=(26, 29, 34))
    d.rectangle([0, 0, round(W * t / total), 8], fill=ACCENT)
    return frame


total = HOOK_DUR + sum(DURS)
ff = subprocess.Popen(
    ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
     "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-crf", "18", "-preset", "medium",
     "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out_path],
    stdin=subprocess.PIPE)

starts = [HOOK_DUR + sum(DURS[:k]) for k in range(len(DURS))]
n = round(total * FPS)
for f in range(n):
    t = f / FPS
    if t < HOOK_DUR:
        frame = hook_frame(t)
    else:
        k = max(k for k in range(len(DURS)) if starts[k] <= t)
        frame = scenes[k].copy()
        lt = t - starts[k]
        if lt < XFADE:  # crossfade from the previous scene with a small upward slide
            prev = hook_frame(HOOK_DUR - 1e-3) if k == 0 else scenes[k - 1]
            a = lt / XFADE
            moved = Image.new("RGB", (W, H), BG)
            moved.paste(frame, (0, round((1 - a) * 50)))
            frame = Image.blend(prev, moved, a)
    ff.stdin.write(np.asarray(progress(frame, t, total)).tobytes())
ff.stdin.close()
ff.wait()
print(out_path, f"{total:.1f}s", n, "frames")
