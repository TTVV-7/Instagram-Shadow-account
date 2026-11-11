"""Turn a World Drive capture (tools/capture_drive.js) into a 9:16 Reel with text, credit and an end card.

Usage: python3 tools/worlddrive_reel.py <fonts-dir> <capture-dir> <out.mp4> "<hook>" "<place>" "<place detail>" [music-seed]
  hook:   big headline over the drop-in, e.g. "We drove on the Moon."
  place:  e.g. "Mons Huygens"; place detail: e.g. "The Moon · the Apennines' highest peak"
Silent video is written to <out>-silent.mp4, then music (tools/make_music.py) is mixed in at -14 LUFS.
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS, CAP, OUT, HOOK, PLACE, DETAIL = sys.argv[1:7]
SEED = int(sys.argv[7]) if len(sys.argv) > 7 else 1
W, H, FPS = 1080, 1920, 30
ACCENT, TEXT, BG = "#FFD23F", "#FFFFFF", (11, 13, 16)
SAFE_TOP, SAFE_BOTTOM = 220, 420  # Instagram's header and caption/buttons
HOOK_SECONDS, END_SECONDS = 3.2, 3.5

info = json.load(open(os.path.join(CAP, "capture.json")))
frames = sorted(f for f in os.listdir(os.path.join(CAP, "frames")) if f.endswith(".jpg"))
CREDIT = info.get("credit", "")


def font(name, size, wght):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    f.set_variation_by_axes([wght])
    return f


SG = "SpaceGrotesk%5Bwght%5D.ttf"
JM = "JetBrainsMono%5Bwght%5D.ttf"
HOOK_F = font(SG, 104, 700)
PLACE_F = font(SG, 64, 700)
DETAIL_F = font(SG, 38, 500)
KICK_F = font(JM, 30, 700)
CREDIT_F = font(SG, 22, 500)


def wrap(d, text, f, width):
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if d.textlength(trial, font=f) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + ([line] if line else [])


def shadowed(base, draw_fn):
    """Draw text with a soft dark shadow so it reads on bright lunar ground and sky."""
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(shadow), (0, 0, 0, 200))
    base.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(10)))
    draw_fn(ImageDraw.Draw(base), None)


def hook_layer():
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lines = wrap(d, HOOK, HOOK_F, W - 140)

    def paint(dd, shadow):
        y = SAFE_TOP + 40
        dd.text((70, y), "WORLD DRIVE", font=KICK_F, fill=shadow or ACCENT)
        y += 56
        for ln in lines:
            dd.text((70, y), ln, font=HOOK_F, fill=shadow or TEXT)
            y += 116

    shadowed(layer, paint)
    return layer


def place_layer():
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    def paint(dd, shadow):
        y = SAFE_TOP + 40  # above the vehicle, which sits in the lower middle of the chase view
        dd.rounded_rectangle((70, y, 70 + 14, y + 110), 7, fill=shadow or ACCENT)
        dd.text((104, y - 6), PLACE, font=PLACE_F, fill=shadow or TEXT)
        dd.text((106, y + 70), DETAIL, font=DETAIL_F, fill=shadow or (230, 230, 230))

    shadowed(layer, paint)
    return layer


def credit_layer():
    """The map's credit, as the app shows it (Google's terms for Earth; NASA's data for the Moon)."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if not CREDIT:
        return layer
    d = ImageDraw.Draw(layer)
    lines = wrap(d, CREDIT, CREDIT_F, W - 140)
    y = H - SAFE_BOTTOM + 8
    for ln in lines[:3]:
        tw = d.textlength(ln, font=CREDIT_F)
        d.rounded_rectangle((W - 70 - tw - 14, y - 4, W - 70 + 8, y + 28), 8, fill=(0, 0, 0, 140))
        d.text((W - 70 - tw - 4, y), ln, font=CREDIT_F, fill=(255, 255, 255, 230))
        y += 34
    return layer


def end_card(last):
    bg = last.filter(ImageFilter.GaussianBlur(28)).convert("RGBA")
    bg.alpha_composite(Image.new("RGBA", (W, H), (*BG, 175)))
    d = ImageDraw.Draw(bg)
    y = H // 2 - 330
    d.text((W // 2, y), "WORLD DRIVE", font=font(SG, 120, 700), fill=ACCENT, anchor="mm")
    y += 130
    for ln in ["Pick anywhere on Earth", "— or the Moon.", "Drop in. Drive."]:
        d.text((W // 2, y), ln, font=font(SG, 58, 600), fill=TEXT, anchor="mm")
        y += 74
    y += 50
    pill_f = font(SG, 54, 700)
    label = "worlddrive.app"
    tw = d.textlength(label, font=pill_f)
    d.rounded_rectangle((W // 2 - tw / 2 - 44, y - 50, W // 2 + tw / 2 + 44, y + 50), 50, fill=ACCENT)
    d.text((W // 2, y), label, font=pill_f, fill=BG, anchor="mm")
    y += 110
    d.text((W // 2, y), "Free in your browser · no download", font=font(SG, 40, 500), fill=(220, 220, 220), anchor="mm")
    return bg.convert("RGB")


def main():
    silent = OUT.rsplit(".", 1)[0] + "-silent.mp4"
    hook, place, credit = hook_layer(), place_layer(), credit_layer()
    drive_start = info.get("driveStart", 0)
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", silent],
        stdin=subprocess.PIPE)
    hook_frames = int(HOOK_SECONDS * FPS)
    last = None
    for i, name in enumerate(frames):
        img = Image.open(os.path.join(CAP, "frames", name)).convert("RGB")
        if img.size != (W, H):
            img = img.resize((W, H), Image.LANCZOS)
        frame = img.convert("RGBA")
        frame.alpha_composite(credit)
        if i < hook_frames:
            a = 1.0 if i < hook_frames - 8 else (hook_frames - i) / 8
            frame.alpha_composite(Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 0)), hook, a))
        if i >= max(drive_start, hook_frames):
            a = min(1.0, (i - max(drive_start, hook_frames)) / 10)
            frame.alpha_composite(Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 0)), place, a))
        last = frame.convert("RGB")
        enc.stdin.write(last.tobytes())
    card = end_card(last)
    for i in range(int(END_SECONDS * FPS)):
        a = min(1.0, i / 9)
        enc.stdin.write(Image.blend(last, card, a).tobytes())
    enc.stdin.close()
    enc.wait()

    seconds = len(frames) / FPS + END_SECONDS
    here = os.path.dirname(os.path.abspath(__file__))
    wav = OUT.rsplit(".", 1)[0] + "-music.wav"
    subprocess.run([sys.executable, os.path.join(here, "make_music.py"), wav, f"{seconds + 0.5:.2f}", str(SEED)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", wav, "-filter_complex",
                    f"[1:a]afade=t=out:st={seconds - 1.5:.2f}:d=1.5,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", OUT], check=True)
    os.remove(wav)
    print(OUT, f"{seconds:.1f}s")


main()
