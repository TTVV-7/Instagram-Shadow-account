# World Drive Reels (on @printyours.ca, Wed + Sat)

Ads for **World Drive** (worlddrive.app, the account owner's own game): a free browser game where you
pick anywhere on Earth, or the Moon, drop in and drive it in 3D. Approved by the owner on Nov 11,
2026: two World Drive Reels a week on @printyours.ca, posted automatically like the news Reels.

- **Wednesday: the Moon.** No map cost.
- **Saturday: Earth.** Uses the owner's Google Maps key (`google_api` in the environment; the owner
  approved it, about 1–2 drives a week). Each recorded drive is billed by Google.

## Each Reel: the stunt montage (since Nov 13)

Why: the owner's own World Drive Reels got 1,400–1,800 views; the slow single-place drive (Apollo 11)
got 131, with 58% swiping away in the first seconds (a flat grey opening, no action, no voice). The
montage copies what worked in the owner's best Reel (DfI_V6gRYSF): action from frame 1, a cut every
~4 s across famous places, the game's own stunt call-outs, short all-caps captions, a voiceover.

1. **3 places, ~4 s each**, recorded in one page load with `tools/capture_montage.js` (full boost,
   hard steering into walls, hops). Open on the most chaotic clip (a spin / big air / crash).
   Skip places that look flat or empty (the Grand Canyon rim road and most Moon maria do).
2. **Captions**: one short all-caps line per cut, the place name small above it, e.g.
   "THE REAL WORLD." / "FLOOR IT." / "OOPS." / "WRONG LANE." / "NO BRAKES." Vary them.
3. **Voiceover** (biggest lever): vidIQ `vidiq_voiceover_generate`, voice "Roger - Laid-Back"
   (voiceId CwhRBWXzGAHq8TQ4Fs17) unless the owner adds a cloned voice in vidIQ (isCustom: use it).
   Deadpan developer tone, ~35–40 words, ~15 s, names the places in cut order, ends with
   "World Drive dot app". E.g. "So I made a game where you can drive anywhere on Earth. Times Square.
   The Golden Gate. Monaco. Real places. Very bad driving. It's free, right in your browser. World
   Drive dot app." Write a new line each time (Moon: "…I put the Moon in it. Low gravity. Bad idea.").
4. **End card** 3 s: WORLD DRIVE · worlddrive.app · Free in your browser. Total ~15–16 s; the video
   must be at least 0.5 s longer than the voiceover.
5. Map credit stays on screen (it's in the captured frames).

Caption: first person ("I made a game where you can…"), the places, "Free in your browser →
worlddrive.app", and a question ("Where should I crash next? Comment a place 👇"). No AI label
(real gameplay; the voice is synthetic but the footage isn't AI-generated imagery).

## How to make one

World Drive's code is in TTVV-7/Neptune-digital-twin (default branch claude/kind-ride-ovicsk). The
capture hook (`window.worldDriveCapture`, dev server only) is on branch `claude/youthful-rubin-qgrl5i`
there; rebase it onto the default branch first so the Reel shows the latest game.

```bash
# 1. World Drive's dev server (Neptune-digital-twin checkout, hook branch)
npm ci --ignore-scripts                                  # once per container
npx vite --config vite.drive.config.js --port 5199 --strictPort                    # Earth: uses google_api
env -u google_api npx vite --config vite.drive.config.js --port 5199 --strictPort   # Moon only
# 2. Record 4 places x 5 s (pick the best 3 after), ~25 min without a GPU
node tools/capture_montage.js <dir> manhattan,golden-gate,monaco,shibuya 5 <seed>
# 3. Voiceover: vidiq_voiceover_generate -> download the mp3 into the post folder
# 4. Cut it: spec.json picks clip order, start, length and captions (see the Nov 14 post)
python3 tools/worlddrive_montage.py <fonts-dir> <dir> posts/<date>-worlddrive-<slug>/spec.json posts/<date>-worlddrive-<slug>/reel.mp4
```

Look at a contact sheet of each clip (frames ~20, 75, 140) before choosing cuts and the opener.
The older single-drive tools (capture_drive.js, worlddrive_reel.py) still work but aren't used.

Posting: Instagram rejects a raw GitHub URL. Push the reel, import its raw URL with vidIQ's
`vidiq_video_upload`, then publish the returned vidIQ `videoUrl` with `vidiq_instagram_publish_reel`.

Fonts: Space Grotesk + JetBrains Mono (+ Inter for news slides) from github.com/google/fonts (`ofl/spacegrotesk`, `ofl/jetbrainsmono`).
Check stills from the hook, the drive and the end card before posting.

## Places

Never repeat a place; log each one below. Ideas by series:
- **Moon** (spot ids): Apollo sites (moon-apollo-11, -12, -14, -15, -16, -17), moon-tycho,
  moon-copernicus, moon-aristarchus, moon-plato, moon-huygens, moon-shackleton, moon-orientale,
  moon-tsiolkovskiy (far side), moon-change-4 (far side), moon-chandrayaan-3, moon-clavius,
  moon-mons-hadley, moon-montes-apenninus, moon-vallis-schroteri, moon-south-pole, moon-north-pole …
- **Earth** spot ids: golden-gate, lions-gate, sea-to-sky, manhattan, monaco, shibuya, furka,
  grand-canyon, sydney, arc, vegas. Then any landmark by "lat,lon,earth,Name" (big cities have the
  best 3D). Later: places commenters ask for ("You pick, we drive").

| Date | World | Place | Link |
|---|---|---|---|
| 2026-11-11 | Moon | Tranquility Base (moon-apollo-11) | https://www.instagram.com/reel/DfoG7NEq5WS/ |
| 2026-11-14 | Earth | Times Square, Golden Gate Bridge, Monaco harbour (montage) | (Saturday) |
