# Content plan — @printyours.ca · "a day in 3D" series

Account: **@printyours.ca** (existing account; already connected to vidIQ and Zapier).
"a day in 3D" is the series name on the slides, not the handle.

## Mix: 3D printing, 2 AI × 3D printing days, 2 World Drive days

| Day | Post |
|---|---|
| Mon | 3D printing news |
| Tue | AI × 3D printing |
| Wed | World Drive Reel: the Moon (see docs/worlddrive-reels.md) |
| Thu | 3D printing news |
| Fri | AI × 3D printing |
| Sat | World Drive Reel: Earth (see docs/worlddrive-reels.md) |
| Sun | 3D printing news + weekly recap carousel |

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

### Voiceover providers (owner approved both, Nov 15)
0. Google Cloud Text-to-Speech (owner approved, Nov 16): `python3 tools/google_tts.py <out.mp3> "<script>"`,
   voice en-US-Chirp3-HD-Charon, rate 1.08, on the `google_api` key. Likely free (free tier ~1M chars/month).
   Needs the Cloud Text-to-Speech API enabled on Google Cloud project 979605278581; until then it errors
   with PERMISSION_DENIED, so fall through to the next provider.
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
