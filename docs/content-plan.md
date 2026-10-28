# Content plan — @printyours.ca · "a day in 3D" series

Account: **@printyours.ca** (existing account; already connected to vidIQ and Zapier).
"a day in 3D" is the series name on the slides, not the handle.

## Mix: purely 3D printing, with 2 AI × 3D printing days

| Day | Post |
|---|---|
| Mon | 3D printing news |
| Tue | AI × 3D printing |
| Wed | 3D printing news |
| Thu | 3D printing news |
| Fri | AI × 3D printing |
| Sat | 3D printing news |
| Sun | 3D printing news + weekly recap carousel |

AI × 3D printing topics — **AI 3D modeling is the priority**: text-to-3D and image-to-3D tools,
generative CAD, AI-generated printable models. Also: AI slicers and print settings,
print-failure detection, AI in print farms.

### "AI → Print" series (one AI day per week)
Generate a model with an AI tool (e.g. hi3D image-to-3D → GLB), print it, and post the result on the
"Worth it?" slide: AI image + photo of the print + verdict (is it actually printable?).
Pair with a short Reel of the print. If these perform, move from 2 to 3 AI days.

## Formats
**Current priority (low follower count): a Reel every day + the weekly recap carousel on Sunday.**
Reels reach non-followers; carousels mostly reach existing followers. Daily carousels come back once
the account has a few hundred followers.

- **Daily Reel (main format):** ~40–45s, 1080×1920, made with `tools/render_reel.py`.
  Hook scene (story image + headline naming who did what, visible from frame 1) → What happened →
  Quick explainer of any tool/company → How it works → Why it matters → Cost/details → Our take
  (hi3D + Claude → OrcaSlicer → Bambu / Snapmaker) → CTA. 6–7s per text scene.
  Rendered silent: add a trending sound (↗) in the Instagram app when posting, turn on the AI label.
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
- Every post is approved before publishing (slides + caption + account).
- Routes: Zapier (Instagram for Business) → fallback Meta Business Suite upload/schedule.
- Reels via vidIQ: turn the weekly carousel into a swipe-style Reel for reach.
