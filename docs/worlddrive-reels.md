# World Drive Reels (on @printyours.ca, Wed + Sat)

Ads for **World Drive** (worlddrive.app, the account owner's own game): a free browser game where you
pick anywhere on Earth, or the Moon, drop in and drive it in 3D. Approved by the owner on Nov 11,
2026: two World Drive Reels a week on @printyours.ca, posted automatically like the news Reels.

- **Wednesday: the Moon.** No map cost.
- **Saturday: Earth.** Uses the owner's Google Maps key (`google_api` in the environment; the owner
  approved it, about 1–2 drives a week). Each recorded drive is billed by Google.

## Each Reel

Real gameplay only (never AI images of the game): a scripted drive recorded from World Drive itself.
The globe → drop in → drive → end card, ~25–30 s:

1. **Hook** (first ~3 s, over the drop-in): "WORLD DRIVE" kicker + a headline naming the place, e.g.
   "We drove where Apollo 11 landed." / "We dropped onto the Golden Gate Bridge."
2. **Drive** (~18 s): boost, weave, hop; the place name and a one-line detail in the lower corner.
3. **End card**: "Pick anywhere on Earth — or the Moon. Drop in. Drive." + **worlddrive.app** +
   "Free in your browser · no download".
4. Original music (`tools/make_music.py`, a new seed each time), -14 LUFS.
5. The map credit stays on screen the whole time (`capture.json` → `credit`): Google's data
   providers on Earth (Google's terms require it), NASA LRO on the Moon.

Caption: what we drove + one fun fact about the place + "Drive it yourself free at worlddrive.app"
+ a question ("Where should we drop in next? Comment a place 👇"). Hashtags: #worlddrive #moon or the
city + #browsergame #3dmaps. Instagram's AI label is NOT needed: it's real gameplay, not AI imagery.

## How to make one

World Drive's code is in TTVV-7/Neptune-digital-twin. The capture hook (`window.worldDriveCapture`,
dev server only) is on branch `claude/youthful-rubin-qgrl5i` there (until merged).

```bash
# 1. World Drive's dev server (in the Neptune-digital-twin checkout, on the branch with the hook)
npm ci --ignore-scripts                                  # once per container
env -u google_api npx vite --config vite.drive.config.js --port 5199 --strictPort   # Moon: no Google key
npx vite --config vite.drive.config.js --port 5199 --strictPort                    # Earth: uses google_api
# 2. Record (half size, ~1–2 s per frame without a GPU: ~15–25 min)
node tools/capture_drive.js <capture-dir> <place> 18 1
#   place: a spot id (moon-tycho, golden-gate) or "lat,lon,earth|moon,Name"
# 3. Build the Reel (upscales to 1080x1920, adds text, credit, end card, music)
python3 tools/worlddrive_reel.py <fonts-dir> <capture-dir> posts/<date>-worlddrive-<slug>/reel.mp4 "<hook>" "<place>" "<detail>" <seed>
```

Fonts: Space Grotesk + JetBrains Mono from github.com/google/fonts (`ofl/spacegrotesk`, `ofl/jetbrainsmono`).
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
