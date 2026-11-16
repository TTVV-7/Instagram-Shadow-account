"""Free local voiceover with Kokoro (open-source TTS, Apache-2.0), no account or credits.

Usage: <venv>/bin/python tools/kokoro_tts.py <out.mp3> "<script>" [voice] [speed]
  voice: Kokoro voice id, default am_michael (others: am_fenrir, am_puck, am_adam, af_heart, ...)
  speed: 1.0 = normal; 1.1 suits Reels.
Setup (once per container, the owner approved it on Nov 16):
  python3 -m venv $VENV && $VENV/bin/pip install kokoro-onnx soundfile
  model files in $KOKORO_DIR (default: ~/kokoro-model): kokoro-v1.0.int8.onnx and voices-v1.0.bin from
  https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
"""
import os
import subprocess
import sys
import tempfile

import soundfile as sf
from kokoro_onnx import Kokoro

out, script = sys.argv[1], sys.argv[2]
voice = sys.argv[3] if len(sys.argv) > 3 else "am_michael"
speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.1
d = os.environ.get("KOKORO_DIR", os.path.expanduser("~/kokoro-model"))
kokoro = Kokoro(os.path.join(d, "kokoro-v1.0.int8.onnx"), os.path.join(d, "voices-v1.0.bin"))
samples, rate = kokoro.create(script, voice=voice, speed=speed, lang="en-us")
with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
    sf.write(tmp.name, samples, rate)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-ar", "44100", "-b:a", "192k", out], check=True)
os.remove(tmp.name)
print(out, voice, f"{len(samples) / rate:.1f}s")
