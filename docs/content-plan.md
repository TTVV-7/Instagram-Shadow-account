# Content plan — @printyours.ca · "a day in 3D" series

> **Stopped Nov 24, 2026 (owner's call).** The daily scheduled Reel task is disabled; nothing posts automatically.
> Last Reel: https://www.instagram.com/reel/DgH57ypBv7m/. Everything below is kept for reference.

Account: **@printyours.ca** (existing account; already connected to vidIQ and Zapier).
"a day in 3D" is the series name on the slides, not the handle.

## Mix (since Nov 18): World Drive every day (owner's call; news Reels stopped)

News Reels averaged ~130 views; World Drive Reels 1,400–5,000+. Every day is a World Drive Reel
(docs/worlddrive-reels.md). "What's new" in the game always comes first; otherwise rotate themes so no
two days in a row look alike:

| Day | World Drive theme |
|---|---|
| Mon | What's new / feature spotlight (water, sonic boom, flying, tricks) |
| Tue | Ride showcase: one weird ride in 3 places ("My game has a lawn tractor") |
| Wed | The Moon and planets, showcase rides |
| Thu | What's new / feature spotlight |
| Fri | Trick or stunt of the week (combo, big air, wipeout compilation) |
| Sat | Space tour, or Earth for a new Earth feature / "you pick, I drive" from comments |
| Sun | Best-of / "rate my driving" crash compilation from the week's clips |

Earth costs a Google Maps session per page load: at most two Earth recording sessions a week. The old
news sections below are kept for reference only.

### Rule since Nov 23: every Reel OPENS ON EARTH (the data)
Swipe-away rate in the first seconds decides reach, and it splits cleanly on one thing: the opening shot.

| Opens on | Reels | Swiped away | Views |
|---|---|---|---|
| A famous Earth place | Earth montage, construction, three new rides (Times Square) | 28–37% | 300–7,200 |
| Moon / Mars / asteroid ground | Apollo 11, Moon rides, Mars, Vesta+Ceres, plane mode | 54–61% | 136–1,100 |

Same voice, same length, same editing in both groups — the voice is not the problem. Grey or red dirt
reads as nothing in the first second; Times Square reads instantly.

So: **the first 2–3 s of every Reel are a famous Earth place, mid-stunt**, then the feature (space
included: "Times Square… then I left Earth"). To keep Earth's cost down, record an **Earth bank** in
ONE page load (same ride for every place = one Maps session) of 5–6 famous places
(manhattan, golden-gate, monaco, sydney, arc, shibuya, vegas, grand-canyon), into ~/earth-bank/<date>/
(off the repo; keep the montage.json). Record a new bank on Monday (or when a new ride should star in
it); reuse its clips the rest of the week, a different place each day. Space-only Reels: no more.

AI × 3D printing topics — **AI 3D modeling is the priority**: text-to-3D and image-to-3D tools,
generative CAD, AI-generated printable models. Also: AI slicers and print settings,
print-failure detection, AI in print farms.

### "AI → Print" series (one AI day per week)
Generate a model with an AI tool (e.g. hi3D image-to-3D → GLB), print it, and post the result on the
"Worth it?" slide: AI image + photo of the print + verdict (is it actually printable?).
Pair with a short Reel of the print. If these perform, move from 2 to 3 AI days.

## Performance notes (Nov 13, from Instagram insights)

- Best: the owner's own clips: World Drive gameplay with voiceover (1,400–1,800 views) and real prints,
  8–17 s (1,400+ views, 60% watched). Automated 44 s text-slide news Reels: ~130 views, 5–9% watched,
  ~80% swipe away in the first seconds.
- So: shorter (≤15–20 s), motion in the first second, a voiceover, real footage/photos over text slides.
  World Drive Reels use the stunt montage (docs/worlddrive-reels.md).
- Nov 15: the World Drive stunt montage hit 1,603 views, 91% watched, 21% skip. The 18 s mBox news
  Reel: 133 views, 21% watched, 70% skip — shorter fixed watch time, but the hook still loses people.

## News Reel hooks (since Nov 15) — tools/news_reel.py

What top 3D-printing Reels (100K–1.7M views, Aug–Nov 2026) do in the first 2 s, and what ours lacked:
- **Talk to the viewer, not about the company.** "This is why your curved prints look cheap",
  "Stop putting your fingers on your build plate", "3 wrong slicer settings you should always change".
  Ours were "Creality made…", "Raise3D's new printer…": a headline, not a reason to stay.
- **The payoff on screen in frame 1**: the printed thing, the kid with the printer, the giant machine —
  full screen, moving. Not a still photo with a logo and a label pill (reads as an ad).
- **The voice says the hook immediately**, and big word-by-word captions follow it (most people watch muted).

Hook formulas (≤ 8 words, on screen AND the first sentence of the voiceover, no brand name first):
1. You/your + concrete outcome: "Your kid can now 3D print the family dog."
2. Stop / don't: "Stop buying a bigger printer. Read this first."
3. Surprising number or size, made personal: "This printer is taller than you." / "$349 for four colours."
4. Question that names the viewer's pain: "Tired of babysitting your prints?"
5. "This is why…" / "Nobody tells you…" for a how-it-works angle.
Then: what it is (one line, brand here), one key fact, a comment question. ~35–45 words, ~15–18 s.

Build: tools/news_reel.py with 3–6 real images (press/product photos; lifestyle shot with people or the
printed object first, `"fill": true` + focus for photos, plain path for product cutouts), cuts every 2 s,
voiceover from vidIQ (Roger), captions synced to it, 2 s CTA end card. hi3D images only when the story
has no real visuals (then the AI label is ON). The old slide format (render_reel.py) is retired for news.

### Voiceover providers
**Default since Nov 18: the owner's own cloned voice, energetic** (owner's choice). `~/.venvs/chatterbox/bin/python
tools/clone_tts.py <out.mp3> "<script>" 0.7 0.35` (Chatterbox, MIT, free, ~90 s on CPU). The reference
recording is the owner's voice memo at ~/voice/owner-ref.wav — private, never commit it or any raw copy.
If the venv or the reference is missing (new machine), fall back to the list below and tell the owner
(the reference has to be re-sent; the venv setup is in the script's docstring).

Fallbacks: (owner approved both, Nov 15)
0. Google Cloud Text-to-Speech (owner approved, Nov 16): `python3 tools/google_tts.py <out.mp3> "<script>"`,
   voice en-US-Chirp3-HD-Charon, rate 1.08, on the `google_api` key. Likely free (free tier ~1M chars/month).
   Needs the Cloud Text-to-Speech API enabled on Google Cloud project 979605278581; until then it errors
   with PERMISSION_DENIED, so fall through to the next provider.
0b. Free local voice, Kokoro (open-source, owner approved the install on Nov 16): `$VENV/bin/python
   tools/kokoro_tts.py <out.mp3> "<script>" am_michael 1.1` (setup steps in the script). No credits.
1. vidIQ `vidiq_voiceover_generate`, voice "Roger" (CwhRBWXzGAHq8TQ4Fs17): 28 credits per voiceover.
2. Fallback when vidIQ is out of credits: Higgsfield `generate_audio`. Check `get_cost: true` first.
   seed_audio, preset voice "Grady" (e2a2d2e6-9ed2-59cd-82af-feaa27f8a678): 2.1 credits;
   text2speech_v2 variant cozy_voice, same voice: 0.35 credits (cheapest). Use seed_audio when
   the balance allows, else cozy_voice. Keep one voice per series where possible.
3. If neither has credits: don't post a silent news Reel — keep it as a DRAFT with the reason and tell
   the owner (they can send a voice memo of the script instead).

## Formats
**Current priority (low follower count): a Reel every day + the weekly recap carousel on Sunday.**
Reels reach non-followers; carousels mostly reach existing followers. Daily carousels come back once
the account has a few hundred followers.

- **Daily Reel (main format):** ~40–45s, 1080×1920, made with `tools/render_reel.py`.
  Hook scene (story image + headline naming who did what, visible from frame 1) → What happened →
  Quick explainer of any tool/company → How it works → Why it matters → Cost/details → Our take
  (hi3D + Claude → OrcaSlicer → Bambu / Snapmaker) → CTA. 6–7s per text scene.
  Audio: every Reel gets an original background track baked in (`tools/make_music.py <out.wav> <seconds> <seed>`,
  then mux with ffmpeg + loudnorm to -14 LUFS), so it can be posted automatically via vidIQ with the AI label.
  A trending sound added in the app still gives the most reach when there's time to post manually.
- **Daily post:** 5-slide carousel, one image + text slides (no extra image cost):
  1. Cover (image). Headline names WHO did WHAT (e.g. "Meshy's AI now preps your prints"), never a vague tagline.
  2. What happened: 2 short paragraphs in full sentences. Explain any company/tool a casual maker might not know.
  3. How it works / key details: 3–4 numbered rows, each a full phrase.
  4. Why it matters: what it means for people who print + cost/availability + My take.
  5. CTA: comment question + "Need something printed? DM us".
  Kicker = `3D PRINTING` or `AI × 3D PRINTING`.
- **Weekly recap carousel (Sun):** Cover (top story) → 3 Story slides → Quick Hits → CTA.
  Reuses that week's daily images (no new generation).
- CTA adds: "Need something printed? DM us."

## Template changes to make in Figma (pending edit-limit reset)
- Handle `@adayin3d` → `@printyours.ca` (component property default)
- Daily single-post variant: "TODAY" + date instead of issue number
- Story image slot → ~4:3 so 3:4 daily images crop cleanly
- Earlier readability fixes: Worth It hint text, CTA prompt padding, Quick Hits 44 px

## Images (hi3D)
- Model: Nano-Banana 2 (4 pts). Seedream v4.5 (3 pts) as fallback if credits get tight.
- Budget: ~40 images/month incl. rerolls ≈ 160 pts of the 1,000/month.
- Prompt pattern: *cinematic close-up, dark moody workshop, lime green rim light, shallow depth
  of field, photorealistic, high contrast, subject centered with space above and below, no text,
  no logos* + story subject.
- Use press-kit photos when a story names a specific product; turn on Instagram's "AI info" label
  for generated images.

## Posting
- Daily Reels post automatically (approved by the account owner, Nov 10): a daily scheduled task at
  7:40pm Vancouver time renders the Reel and posts it via vidIQ with the AI label on. If posting fails,
  the Reel is left as a DRAFT with the reason in its caption.md.
- Other posts (weekly carousel, one-offs) are still approved before publishing.
- Routes: Zapier (Instagram for Business) → fallback Meta Business Suite upload/schedule.
- Reels via vidIQ: turn the weekly carousel into a swipe-style Reel for reach.
