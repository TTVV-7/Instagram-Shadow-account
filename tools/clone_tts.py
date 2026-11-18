"""Voiceover in the owner's own cloned voice with Chatterbox (Resemble AI, MIT license), free and local.

Usage: ~/.venvs/chatterbox/bin/python tools/clone_tts.py <out.mp3> "<script>" [exaggeration] [cfg_weight]
  exaggeration: 0.25 calm ... 0.5 normal ... 0.8 energetic (default 0.5)
  cfg_weight:   pacing/adherence; lower (0.3) = faster, looser delivery (default 0.4)
The reference recording is the owner's voice memo, kept OFF the repo (the repo is public):
  $OWNER_VOICE, default ~/voice/owner-ref.wav (mono 24 kHz, ~20 s, pauses trimmed, loudness-normalized).
Setup (once per machine; the owner approved it on Nov 18):
  python3 -m venv ~/.venvs/chatterbox && ~/.venvs/chatterbox/bin/pip install chatterbox-tts
Runs on CPU (slow: a few minutes for a 15 s line). The first run downloads the model from Hugging Face.
"""
import os
import subprocess
import sys
import tempfile

import torch
import torchaudio
from chatterbox.tts import ChatterboxTTS

out, script = sys.argv[1], sys.argv[2]
exaggeration = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
cfg = float(sys.argv[4]) if len(sys.argv) > 4 else 0.4
ref = os.environ.get("OWNER_VOICE", os.path.expanduser("~/voice/owner-ref.wav"))
if not os.path.exists(ref):
    sys.exit(f"no reference voice at {ref}")

torch.set_num_threads(os.cpu_count() or 4)
model = ChatterboxTTS.from_pretrained(device="cpu")
wav = model.generate(script, audio_prompt_path=ref, exaggeration=exaggeration, cfg_weight=cfg)
with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
    torchaudio.save(tmp.name, wav, model.sr)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-af", "loudnorm=I=-16:TP=-2", "-ar", "44100", "-b:a", "192k", out], check=True)
os.remove(tmp.name)
print(out, f"{wav.shape[-1] / model.sr:.1f}s", f"exaggeration={exaggeration}", f"cfg={cfg}")
