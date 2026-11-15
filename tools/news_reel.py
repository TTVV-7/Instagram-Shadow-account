"""Fast 9:16 news Reel: full-screen product images in constant motion, word-by-word captions synced
to a voiceover, a viewer-first hook in frame 1, and a 2 s CTA end card. No text slides, no logo up front.

Usage: python3 tools/news_reel.py <fonts-dir> <spec.json> <out.mp4>

spec.json:
  {
    "hook": "YOUR KID CAN 3D PRINT THE DOG",      big text on screen for the first ~2.5 s (≤ 7 words)
    "voiceover": "posts/.../voiceover.mp3",
    "script": "Your kid can now 3D print the dog. ...",   exactly what the voiceover says
    "images": ["posts/.../images/a.png", ...],   3-6 product shots; cut every ~2 s, cycling
    "cta": "Would you let your kid run one?",      end card question
    "credit": "Photos: Creality",                small, bottom
    "music_seed": 31
  }
Captions: the script is split into sentences; sentence starts are matched to the pauses in the
voiceover (ffmpeg silencedetect), and words inside a sentence are timed by their length.
"""
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS, SPEC, OUT = sys.argv[1:4]
spec = json.load(open(SPEC))
W, H, FPS = 1080, 1920, 30
ACCENT, TEXT, BG = "#C6FF3D", "#FFFFFF", (11, 13, 16)
SAFE_TOP, SAFE_BOTTOM = 230, 430
CUT_S = spec.get("cut_seconds", 2.0)
END_S = spec.get("end_seconds", 2.2)
HOOK_S = spec.get("hook_seconds", 2.6)


def font(name, size, wght):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    f.set_variation_by_axes([wght])
    return f


SG = "SpaceGrotesk%5Bwght%5D.ttf"
HOOK_F = font(SG, 112, 700)
CAP_F = font(SG, 84, 700)
SMALL_F = font(SG, 26, 500)


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                capture_output=True, text=True, check=True).stdout.strip())


def pauses(path):
    """Midpoints of silences >= 0.12 s in the voiceover."""
    err = subprocess.run(["ffmpeg", "-i", path, "-af", "silencedetect=noise=-35dB:d=0.12", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return [(s + e) / 2 for s, e in zip(starts, ends)], (ends[0] if starts and starts[0] < 0.05 and ends else 0.0)


def word_times(script, voice, offset):
    """[(word, start, end)] for the captions, in video time."""
    total = duration(voice)
    mids, lead = pauses(voice)
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", script.strip()) if s.strip()]
    # Sentence boundaries: the pause nearest to where its share of characters says it should fall.
    chars = [len(s) for s in sentences]
    bounds, acc = [lead], 0
    for c in chars[:-1]:
        acc += c
        guess = lead + (total - lead) * acc / sum(chars)
        bounds.append(min(mids, key=lambda m: abs(m - guess)) if mids else guess)
    bounds.append(total)
    out = []
    for i, s in enumerate(sentences):
        words = s.split()
        a, b = bounds[i], max(bounds[i + 1], bounds[i] + 0.3)
        span = (b - a) * 0.95
        weights = [len(w) + 2 for w in words]
        t = a
        for w, k in zip(words, weights):
            d = span * k / sum(weights)
            out.append((w, t + offset, t + d + offset))
            t += d
    return out


def chunks(words, n=3):
    """Group words into caption chunks of up to n words (break after punctuation)."""
    out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) == n or re.search(r"[.,!?;:]$", w[0]):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return [(" ".join(x[0] for x in c), c[0][1], c[-1][2], c) for c in out]


def cover(img, k, dx, dy):
    """Scale img to cover W x H, zoom k, offset (dx, dy) in [-1, 1] of the slack."""
    s = max(W / img.width, H / img.height) * k
    w, h = img.width * s, img.height * s
    x = (W - w) / 2 + dx * (w - W) / 2
    y = (H - h) / 2 + dy * (h - H) / 2
    return img.resize((int(w), int(h)), Image.BILINEAR), int(x), int(y)


def fill_crop(src, focus_x=0.5, focus_y=0.5):
    """A photo filling the whole 9:16 frame, cropped around (focus_x, focus_y) of the image."""
    im = Image.open(src).convert("RGB")
    s = max(W / im.width, H / im.height) * 1.05
    w, h = int(im.width * s), int(im.height * s)
    big = im.resize((w, h), Image.LANCZOS)
    x = min(max(int(focus_x * w - W / 2), 0), w - W)
    y = min(max(int(focus_y * h - H / 2), 0), h - H)
    return big.crop((x, y, x + W, y + H))


def shot(entry):
    """An images[] entry: a path (shown whole over a blur) or {"path", "fill": true, "focus": [x, y]}."""
    if isinstance(entry, dict):
        if entry.get("fill"):
            fx, fy = entry.get("focus", [0.5, 0.5])
            return fill_crop(entry["path"], fx, fy)
        return fit_on_blur(entry["path"])
    return fit_on_blur(entry)


def fit_on_blur(src):
    """A product shot (often on white or transparent) shown whole over a blurred, darkened copy."""
    im = Image.open(src)
    rgba = im.convert("RGBA")
    if im.mode in ("RGBA", "LA") and rgba.getbbox():
        rgba = rgba.crop(rgba.getbbox())
    bg = Image.new("RGB", (W, H), BG)
    b, bx, by = cover(rgba.convert("RGB"), 1.15, 0, 0)
    bg.paste(b.filter(ImageFilter.GaussianBlur(40)).point(lambda v: int(v * 0.45)), (bx, by))
    s = min((W - 40) / rgba.width, (H * 0.62) / rgba.height)
    fg = rgba.resize((int(rgba.width * s), int(rgba.height * s)), Image.LANCZOS)
    canvas = bg.convert("RGBA")
    canvas.alpha_composite(fg, ((W - fg.width) // 2, int(H * 0.40 - fg.height / 2)))
    return canvas.convert("RGB")


def shadow_text(base, xy, text, f, fill, anchor="mm", stroke=8):
    d = ImageDraw.Draw(base)
    d.text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def wrap(text, f, width):
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def main():
    voice = spec["voiceover"]
    vdur = duration(voice)
    offset = 0.15
    words = word_times(spec["script"], voice, offset)
    caps = chunks(words)
    body = max(vdur + offset + 0.4, HOOK_S + 1)
    total = body + END_S
    frames = int(total * FPS)
    shots = [shot(p) for p in spec["images"]]
    credit = spec.get("credit", "")
    silent = OUT.rsplit(".", 1)[0] + "-silent.mp4"
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", silent],
        stdin=subprocess.PIPE)
    hook_lines = wrap(spec["hook"].upper(), HOOK_F, W - 120)
    moves = [(1.0, 1.12, -0.6, 0.6), (1.12, 1.0, 0.6, -0.6), (1.05, 1.18, 0, 0), (1.15, 1.04, -0.5, -0.5)]
    end_card = None
    for f in range(frames):
        t = f / FPS
        if t < body:
            i = int(t / CUT_S)
            k0, k1, dx, dy = moves[i % len(moves)]
            p = (t - i * CUT_S) / CUT_S
            k = k0 + (k1 - k0) * p
            # a quick punch at each cut
            k *= 1 + 0.06 * max(0.0, 1 - (t - i * CUT_S) / 0.18)
            img, x, y = cover(shots[i % len(shots)], k, dx * p, dy * p)
            frame = Image.new("RGB", (W, H), BG)
            frame.paste(img, (x, y))
            frame = frame.convert("RGBA")
            if t < HOOK_S:
                y0 = SAFE_TOP + 40
                for n, ln in enumerate(hook_lines):
                    shadow_text(frame, (W // 2, y0 + n * 124), ln, HOOK_F, ACCENT if n == len(hook_lines) - 1 else TEXT, "mt", 10)
            else:
                cur = next((c for c in caps if c[1] <= t < c[2] + 0.12), None)
                if cur:
                    text, a, b, ws = cur
                    lines = wrap(text.upper(), CAP_F, W - 140)
                    y0 = H - SAFE_BOTTOM - 120 - (len(lines) - 1) * 96
                    for n, ln in enumerate(lines):
                        shadow_text(frame, (W // 2, y0 + n * 96), ln, CAP_F, TEXT, "mm", 9)
            if credit:
                ImageDraw.Draw(frame).text((W - 40, H - SAFE_BOTTOM + 70), credit, font=SMALL_F, fill=(230, 230, 230), anchor="rs",
                                           stroke_width=2, stroke_fill=(0, 0, 0))
            last = frame.convert("RGB")
            enc.stdin.write(last.tobytes())
        else:
            if end_card is None:
                bg = last.filter(ImageFilter.GaussianBlur(26)).convert("RGBA")
                bg.alpha_composite(Image.new("RGBA", (W, H), (*BG, 200)))
                d = ImageDraw.Draw(bg)
                y = H // 2 - 200
                for ln in wrap(spec.get("cta", ""), font(SG, 76, 700), W - 160):
                    d.text((W // 2, y), ln, font=font(SG, 76, 700), fill=TEXT, anchor="mm")
                    y += 92
                d.text((W // 2, y + 60), "COMMENT BELOW ↓", font=font(SG, 40, 700), fill=ACCENT, anchor="mm")
                d.text((W // 2, y + 170), "Follow @printyours.ca for daily 3D printing news", font=font(SG, 36, 500), fill=(220, 220, 220), anchor="mm")
                end_card = bg.convert("RGB")
            a = min(1.0, (t - body) / 0.2)
            enc.stdin.write(Image.blend(last, end_card, a).tobytes())
    enc.stdin.close()
    enc.wait()

    here = os.path.dirname(os.path.abspath(__file__))
    wav = OUT.rsplit(".", 1)[0] + "-music.wav"
    subprocess.run([sys.executable, os.path.join(here, "make_music.py"), wav, f"{total + 0.5:.2f}", str(spec.get("music_seed", 1))],
                   check=True, stdout=subprocess.DEVNULL)
    ms = int(offset * 1000)
    graph = (f"[1:a]volume=0.2,afade=t=out:st={total - 1.0:.2f}:d=1.0[m];[2:a]adelay={ms}|{ms},loudnorm=I=-16:TP=-2[v];"
             f"[m][v]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", wav, "-i", voice, "-filter_complex", graph,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", OUT], check=True)
    os.remove(wav)
    os.remove(silent)
    print(OUT, f"{total:.1f}s")


main()
