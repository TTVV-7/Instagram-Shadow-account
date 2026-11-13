"""Cut a World Drive stunt montage (tools/capture_montage.js) into a fast 9:16 Reel with a voiceover.

Usage: python3 tools/worlddrive_montage.py <fonts-dir> <montage-dir> <spec.json> <out.mp4>

spec.json:
  {
    "captions": ["DRIVE ANYWHERE.", "TIMES SQUARE.", "MONACO.", "OOPS."],   one per clip, big and short
    "voiceover": "path/to/voice.mp3",        optional; mixed over the music
    "music_seed": 7,                          tools/make_music.py seed
    "trim_start": 0.3, "clip_seconds": 4.2,   seconds kept from each clip
    "end_seconds": 2.5
  }
Hard cuts every few seconds, a quick punch-in at each cut, the place name small above the caption,
the game's own stunt call-outs and map credit (already in the frames), then a short end card.
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS, MONT, SPEC, OUT = sys.argv[1:5]
spec = json.load(open(SPEC))
info = json.load(open(os.path.join(MONT, "montage.json")))
W, H, FPS = 1080, 1920, 30
ACCENT, TEXT, BG = "#FFD23F", "#FFFFFF", (11, 13, 16)
SAFE_TOP = 230
TRIM = spec.get("trim_start", 0.3)
CLIP_S = spec.get("clip_seconds", 4.2)
END_S = spec.get("end_seconds", 2.5)


def font(name, size, wght):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    f.set_variation_by_axes([wght])
    return f


SG = "SpaceGrotesk%5Bwght%5D.ttf"
CAP_F = font(SG, 118, 700)
TAG_F = font(SG, 40, 700)


def caption_layer(caption, place):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    words, lines, cur = caption.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=CAP_F) <= W - 120 or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    y = SAFE_TOP + 20

    def paint(dd, shadow):
        yy = y
        if place:
            dd.text((W // 2, yy), place.upper(), font=TAG_F, fill=shadow or ACCENT, anchor="mt")
            yy += 62
        for ln in lines:
            dd.text((W // 2, yy), ln, font=CAP_F, fill=shadow or TEXT, anchor="mt", stroke_width=0)
            yy += 128

    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    paint(ImageDraw.Draw(sh), (0, 0, 0, 235))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)))
    paint(d, None)
    return layer


def end_card(last):
    bg = last.filter(ImageFilter.GaussianBlur(28)).convert("RGBA")
    bg.alpha_composite(Image.new("RGBA", (W, H), (*BG, 185)))
    d = ImageDraw.Draw(bg)
    y = H // 2 - 260
    d.text((W // 2, y), "WORLD DRIVE", font=font(SG, 128, 700), fill=ACCENT, anchor="mm")
    y += 120
    d.text((W // 2, y), "Drive anywhere on Earth.", font=font(SG, 60, 600), fill=TEXT, anchor="mm")
    y += 130
    pill_f = font(SG, 60, 700)
    label = "worlddrive.app"
    tw = d.textlength(label, font=pill_f)
    d.rounded_rectangle((W // 2 - tw / 2 - 48, y - 54, W // 2 + tw / 2 + 48, y + 54), 54, fill=ACCENT)
    d.text((W // 2, y), label, font=pill_f, fill=BG, anchor="mm")
    y += 110
    d.text((W // 2, y), "Free · in your browser", font=font(SG, 44, 500), fill=(225, 225, 225), anchor="mm")
    return bg.convert("RGB")


def punch(img, k):
    """Zoom in by factor k about the centre (the quick punch-in after a cut)."""
    if k <= 1.0001:
        return img
    cw, ch = W / k, H / k
    return img.resize((W, H), Image.BILINEAR, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))


def main():
    silent = OUT.rsplit(".", 1)[0] + "-silent.mp4"
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", silent],
        stdin=subprocess.PIPE)
    captions = spec.get("captions", [])
    # "cuts": [{"clip": 1, "start": 1.0, "seconds": 4.0, "caption": "..."}] picks the order and the
    # moment of each cut; without it every clip is used in order with trim_start/clip_seconds.
    cuts = spec.get("cuts") or [{"clip": i, "start": TRIM, "seconds": CLIP_S, "caption": captions[i] if i < len(captions) else ""}
                                for i in range(len(info["clips"]))]
    last, total = None, 0
    for cut in cuts:
        i = cut["clip"]
        clip = info["clips"][i]
        d = os.path.join(MONT, f"clip-{i}")
        names = sorted(f for f in os.listdir(d) if f.endswith(".jpg"))
        start = int(cut.get("start", TRIM) * FPS)
        names = names[start:start + int(cut.get("seconds", CLIP_S) * FPS)]
        cap = caption_layer(cut.get("caption", ""), clip.get("place", ""))
        for j, n in enumerate(names):
            img = Image.open(os.path.join(d, n)).convert("RGB").resize((W, H), Image.LANCZOS)
            img = punch(img, 1 + 0.08 * max(0, 1 - j / 6))
            frame = img.convert("RGBA")
            frame.alpha_composite(cap)
            last = frame.convert("RGB")
            enc.stdin.write(last.tobytes())
            total += 1
    card = end_card(last)
    for i in range(int(END_S * FPS)):
        enc.stdin.write(Image.blend(last, card, min(1.0, i / 6)).tobytes())
        total += 1
    enc.stdin.close()
    enc.wait()

    seconds = total / FPS
    here = os.path.dirname(os.path.abspath(__file__))
    wav = OUT.rsplit(".", 1)[0] + "-music.wav"
    subprocess.run([sys.executable, os.path.join(here, "make_music.py"), wav, f"{seconds + 0.5:.2f}", str(spec.get("music_seed", 1))],
                   check=True, stdout=subprocess.DEVNULL)
    fade = f"afade=t=out:st={seconds - 1.2:.2f}:d=1.2"
    voice = spec.get("voiceover")
    if voice:
        # Voice up front, music low under it, then the whole mix to -14 LUFS.
        graph = (f"[1:a]volume=0.22,{fade}[m];[2:a]adelay=250|250,loudnorm=I=-16:TP=-2[v];"
                 f"[m][v]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", wav, "-i", voice, "-filter_complex", graph]
    else:
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", wav, "-filter_complex", f"[1:a]{fade},loudnorm=I=-14:TP=-1.5:LRA=11[a]"]
    subprocess.run(cmd + ["-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", OUT], check=True)
    os.remove(wav)
    os.remove(silent)
    print(OUT, f"{seconds:.1f}s")


main()
