"""Voiceover with Google Cloud Text-to-Speech, using the API key in the `google_api` environment variable.

Usage: python3 tools/google_tts.py <out.mp3> "<script>" [voice] [speaking_rate]
  voice: a Google voice name, default en-US-Chirp3-HD-Charon (male, relaxed); list them with
         curl "https://texttospeech.googleapis.com/v1/voices?languageCode=en-US&key=$google_api"
  speaking_rate: 1.0 = normal; 1.08 suits Reels.
Needs the Cloud Text-to-Speech API enabled on the key's Google Cloud project (and allowed in the
key's API restrictions, if it has any). Free tier: about 1M characters a month for these voices.
The key is read from the environment and never printed.
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

out, script = sys.argv[1], sys.argv[2]
voice = sys.argv[3] if len(sys.argv) > 3 else "en-US-Chirp3-HD-Charon"
rate = float(sys.argv[4]) if len(sys.argv) > 4 else 1.08
key = os.environ.get("google_api") or os.environ.get("GOOGLE_API_KEY")
if not key:
    sys.exit("no google_api key in the environment")

body = {
    "input": {"text": script},
    "voice": {"languageCode": "-".join(voice.split("-")[:2]), "name": voice},
    "audioConfig": {"audioEncoding": "MP3", "speakingRate": rate, "sampleRateHertz": 44100},
}
req = urllib.request.Request(
    f"https://texttospeech.googleapis.com/v1/text:synthesize?key={key}",
    data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        audio = json.load(r)["audioContent"]
except urllib.error.HTTPError as e:
    err = json.loads(e.read() or b"{}").get("error", {})
    sys.exit(f"Google TTS error {e.code}: {err.get('status')} {err.get('message', '')[:300]}")
with open(out, "wb") as f:
    f.write(base64.b64decode(audio))
print(out, voice, f"{len(script)} chars")
