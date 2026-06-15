# Veo Video Reference

Use this reference when an Instagram post needs an AI-generated video, especially for Reels, short video posts, looping ambience, product mood footage, or motion backgrounds behind text.

## Current Docs Check

Before calling any Veo API or relying on request fields, check the current official Gemini API video docs at `https://ai.google.dev/gemini-api/docs/video` or the user's provided Google documentation. Model names, billing, regions, limits, and generated-file retention can change.

Prefer `veo-3.1-generate-preview` for Instagram drafts. Use `veo-3.1-fast-generate-preview` only when the user explicitly prioritizes speed or cost over quality.

## API Workflow

Veo generation through Gemini API is asynchronous:

1. Create a long-running video generation operation with `models.generateVideos` or REST `predictLongRunning`.
2. Poll the operation until `done` is true.
3. Download the generated video immediately.
4. Host the MP4 at a stable public HTTPS URL before sending it to Buffer.

Use `GEMINI_API_KEY` from the environment or an equivalent secret store. Never hardcode or commit Gemini credentials.

Generated videos are stored server-side for a limited time. Download them promptly; do not treat Gemini's temporary video URI as a stable Buffer media URL.

## Recommended Instagram Settings

- Model: `veo-3.1-generate-preview`.
- Aspect ratio: `9:16` for Reels and Stories.
- Duration: 6 seconds by default; use 8 seconds when showing a recipe, process, transformation, or multi-step sequence.
- Resolution: start with `720p` for speed/cost; use `1080p` only when quality matters and the docs allow it for the selected duration.
- Number of videos: omit this field unless the current docs explicitly support it. The model returns one video by default.

Veo 3.1 can generate audio natively, but this skill should not request voiceover, dialogue, spoken copy, ambience, or sound effects by default. Request upbeat instrumental music only. Always keep marketing copy as separate overlay text generated outside the video model.

## Creative Fit

Use Veo video only when motion adds value:

- Product ambience, texture, light movement, location mood, process shots, abstract motion, seasonal backgrounds.
- Avoid using video just to decorate a static announcement.
- Prefer original, brand-safe visuals over celebrity, character, logo, or franchise references.

For Instagram Reels, prefer stronger motion than a passive background:

- Open with visual contrast or a problem state in the first second.
- Show a quick transformation, before/after, or progression.
- Use faster camera movement, cuts, ingredient/product movement, or hands-in-frame action.
- Reserve a clean final frame for overlay text or CTA added outside the AI video tool.
- Keep generated video free of readable text, screens, labels, logos, and signage; add copy programmatically in the editor or posting pipeline.

## Generation Script Format

Write Veo prompts as a structured, time-coded generation script. Do this before making the API call. The script should be specific enough that each second has a visual job.

Required structure:

```text
Vertical 9:16, realistic, <duration>-second premium <domain> video.

<Subject and story summary>. <Style and environment>. <Camera and edit language>. <Mood and visual quality>.

0.0-1.0s: <specific visible action, subject, setting, camera angle>.
1.0-2.0s: <specific visible action, subject, setting, camera angle>.
...

Lighting: <specific lighting direction>.
Camera: <specific camera movement and shot types>.
Music: upbeat instrumental only.

Negative prompts: no sound effects, no kitchen ambience, no voiceover, no dialogue, no readable text, no captions, no phones, no screens, no packaging labels, no logos, no signage, no brand names, no faces, no distorted hands, no extra fingers, no watermark, no subtitles.
```

Rules for generation scripts:

- Match the requested duration exactly in the beat sheet. For 8 seconds, cover `0.0-8.0s`.
- Use concise but complete visual beats. Each beat should describe what the viewer sees, not marketing copy.
- Include camera details per beat when they matter: overhead, macro, push-in, quick cut, hero shot.
- Keep all generated text out of the video. Use overlay text after generation.
- Keep audio direction to music only unless explicitly overridden.
- Put all prohibitions in a final `Negative prompts:` line.

Example 8-second recipe script:

```text
Vertical 9:16, realistic, 8-second premium cooking video.

Danish red curry chicken with jasmine rice. Fast, clear cooking montage in a warm modern Scandinavian home kitchen with natural daylight. Dynamic overhead shots, close-up food textures, smooth push-ins, shallow depth of field, appetizing colors, professional recipe-video style.

0.0-1.0s: Raw chicken breast is sliced into bite-size pieces on a clean wooden cutting board. Onion, garlic, and fresh ginger nearby. Tight overhead shot.
1.0-2.0s: Red bell pepper is sliced into thin strips, green beans are trimmed, jasmine rice is rinsed in a glass bowl. Quick clean cuts between actions.
2.0-3.5s: Oil shimmers in a wok. Chopped onion softens. Red curry paste, minced garlic, and grated ginger are stirred together and become fragrant. Rich texture close-ups.
3.5-5.0s: Chicken pieces are added to the wok and quickly brown. Steam rises. Glossy surface detail. Smooth camera push-in.
5.0-6.5s: Coconut milk pours into the wok. Sauce simmers. Red pepper strips and green beans are added. Vibrant red curry bubbles gently. Attractive food close-ups.
6.5-8.0s: Final plated dish in a deep bowl. Fluffy jasmine rice topped with red curry chicken and vegetables. Fresh lime squeezed over the dish. Steam rising. Hero shot with beautiful food styling.

Lighting: practical Scandinavian kitchen light, warm and natural.
Camera: overhead food cinematography, macro texture shots, smooth motion, quick clean edits.
Music: upbeat instrumental only.

Negative prompts: no sound effects, no kitchen ambience, no voiceover, no dialogue, no readable text, no captions, no phones, no screens, no packaging labels, no logos, no signage, no brand names, no faces, no distorted hands, no extra fingers, no watermark, no subtitles.
```

Example action-oriented Reel script for a meal-planning project:

```text
Vertical 9:16, realistic, 6-second premium meal-planning Reel.

Danish meal planning in a warm modern Scandinavian home kitchen. Fast visual transformation from dinner stress to organized ingredients and a fresh plated meal. Dynamic overhead shots, quick clean edits, smooth push-ins, appetizing colors, practical premium recipe-video style.

0.0-1.0s: A messy kitchen counter with scattered ingredients and an open fridge. Quick overhead shot with visual contrast.
1.0-3.0s: Fresh vegetables, grains, and groceries move into organized groups on the counter. Hands place ingredients neatly. Quick clean cuts.
3.0-5.0s: Colorful dinner prep and a fresh plated everyday meal. Smooth push-in and close-up food textures.
5.0-6.0s: Clean final hero frame with appetizing dinner and warm kitchen light, leaving room for programmatic overlay text.

Lighting: warm practical Scandinavian kitchen light.
Camera: dynamic overhead food cinematography, close-up textures, smooth push-ins, quick clean edits.
Music: upbeat instrumental only.

Negative prompts: no sound effects, no ambience, no voiceover, no dialogue, no readable text, no captions, no phones, no screens, no labels, no logos, no signage, no brand names, no faces, no distorted hands, no extra fingers, no watermark, no subtitles.
```

## Overlay Text

Generate overlay text separately from the video prompt. Keep each snippet short enough to fit mobile video safely, usually 2-5 words.

Make overlay copy match the actual video story and product value. Do not use generic placeholders such as "AI klarer ugen" unless the surrounding frames clearly support that claim. For meal-planning products, use a simple progression:

- Problem: dinner planning feels repetitive or last-minute.
- Product shift: the week gets planned.
- Outcome: groceries become easier.
- CTA: try the product.

Return overlay snippets with timing suggestions:

```text
0.2-1.2s: Hvad skal vi spise?
1.4-2.6s: Lav en madplan
2.8-4.2s: Få indkøbslisten
4.6-5.8s: Prøv NemMad gratis
```

Use proper Danish characters in overlay copy. The overlay script reads JSON as UTF-8 and supports characters such as `å`, `æ`, and `ø` when the selected font supports them.

For local MP4 files, add overlays with:

```bash
python3 skills/insta-skill/scripts/overlay_text.py input.mp4 output.mp4 overlays.json
```

The default overlay style is intentionally neutral: Inter-style bold type, compact white rounded card, dark text, thin green underline accent, and subtle shadow. Project-specific colors, copy tone, and CTA wording belong in `~/.local/insta-skill/<project>/style.md`. Animate overlays with a quick fade/slide in, a steady hold, and a quick fade/slide out. Keep overlays light, polished, and editorial rather than large UI badges or generic subtitle bars.

For recipe and food-process videos, prefer the simpler `text` overlay mode: short white text directly on the video with a subtle shadow/stroke, usually in the lower third. This keeps the food visible and feels less like a UI badge.

The JSON file must contain timed snippets:

```json
[
  {"start": 0.2, "end": 1.2, "text": "Hvad skal vi spise?"},
  {"start": 1.4, "end": 2.6, "text": "Lav en madplan"},
  {"start": 2.8, "end": 4.2, "text": "Få indkøbslisten"},
  {"start": 4.6, "end": 5.8, "text": "Prøv NemMad gratis"}
]
```

Optional project-specific overlay colors can be supplied with `--style-json`:

```json
{
  "mode": "card",
  "accent_color": "#16A34A",
  "text_color": "#111827",
  "card_color": "#FFFFFFE0",
  "shadow_color": "#1118272C",
  "y_ratio": 0.145,
  "max_width_ratio": 0.78
}
```

Simple text style:

```json
{
  "mode": "text",
  "text_color": "#FFFFFF",
  "shadow_color": "#111827AA",
  "y_ratio": 0.70,
  "max_width_ratio": 0.82,
  "align": "center",
  "stroke_width_ratio": 0.003,
  "font_size_ratio": 0.044,
  "min_font_size_ratio": 0.032
}
```

## Prompt Structure

Use the generation script format above. Make sure the script includes:

- Subject: what appears on screen.
- Action: specific motion over the clip.
- Environment: setting, time of day, background details.
- Camera: static, slow push-in, pan, handheld, macro, overhead, orbit, quick cuts.
- Style: realistic, editorial, product ad, documentary, clean studio, etc.
- Lighting and color: practical lighting details, not vague mood words only.
- Audio: upbeat instrumental music only. Do not request sound effects, ambience, voiceover, or dialogue unless the user explicitly overrides this rule.
- Duration and format: vertical 9:16, with a beat sheet that exactly matches the requested duration.
- Negative constraints: no readable text, no phones, no screens, no logos, no labels, no signage, no extra hands, no extra fingers, no distorted product labels, no celebrity likeness, no watermark, no subtitles.

## Instagram Asset Guidance

- Prefer vertical 9:16 for Reels and Stories.
- Keep important visual action away from top and bottom UI-safe areas.
- Avoid generated text and screen UI inside the video; add final text programmatically in the editor, design tool, or posting pipeline.
- Generate or extract a still thumbnail when Buffer or Instagram needs a poster image.
- Review the first and last frames if a loop is desired.

## Safety And Rights

Do not prompt for copyrighted characters, protected logos, celebrity likenesses, private people, or fake news-like footage. When the video could be mistaken for real footage of a consequential event, include disclosure guidance in the post package.

## Handoff

When a video is generated, return:

- Final prompt used.
- Model used.
- Duration, aspect ratio, resolution, and audio direction.
- Local file path and public hosted URL.
- Thumbnail path or URL, if available.
- Any visible artifacts or review concerns.
