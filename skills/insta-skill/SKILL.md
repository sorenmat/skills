---
name: insta-skill
description: Project-based Instagram content generation with persistent style guides, saved post records, duplicate-topic checks, Veo video prompts, overlay text, and Buffer publishing workflows. Use when Codex needs to create Instagram posts, Reels, carousels, captions, hashtags, media briefs, or scheduled/draft Buffer posts for a named project such as a domain, brand, product, or account.
---

# Insta Skill

## Overview

Use this skill to create Instagram content for persistent projects stored under `~/.local/insta-skill/<project>`. Each project has a `style.md` guide and saved post records so future posts stay on-brand and avoid repeating the same idea.

## Workflow

1. Resolve the project name from the user request. For a domain, use the normalized domain as the project slug, e.g. `nemmad.com`.
2. Read `references/projects.md`, then use `scripts/project_state.py init <project>` if the project state does not exist.
3. Load `<project>/style.md` and recent `<project>/posts/*.json` before generating content.
4. Clarify the post goal, audience, format, and publish timing. If any are missing, make conservative assumptions and label them.
5. Choose the Instagram format: feed image, carousel, Story, Reel, or short video post. Prefer Reels/video only when motion strengthens the message.
6. Produce the content package:
   - Hook and main caption.
   - CTA.
   - Hashtag set grouped by branded, niche, and discovery tags.
   - Alt text or accessibility notes.
   - Visual brief or asset prompt.
   - Overlay text snippets for video/carousel assets, when useful.
   - First comment, if useful.
7. Create a normalized `topic_fingerprint` from the post's core hook, topic, audience, and value proposition. Run `scripts/project_state.py check-duplicate <project> <topic_fingerprint>` before finalizing.
8. If a Reel or background video is needed, read `references/veo-video.md` before prompting or calling any Veo video workflow.
9. After generating video, add overlay copy in post-processing when text is needed. Use `scripts/overlay_text.py` for local MP4 files.
10. Save the post record with `scripts/project_state.py save-post <project> <post-json>` using status `idea`, `drafted`, `rendered`, `buffer_draft`, `scheduled`, `published`, or `rejected` as appropriate.
11. If scheduling or publishing through Buffer is requested, read `references/buffer.md` before preparing API calls or manual steps.
12. Before any live post, schedule, or API write, show the final caption, media URL(s), target channel, scheduled time, and ask for explicit approval unless the user has already approved that exact action in the current turn.

## Content Rules

- Keep captions specific to the audience and offer. Avoid generic engagement bait.
- Do not invent facts, prices, dates, claims, availability, partnerships, reviews, metrics, or endorsements.
- Treat brand names, trademarks, people, music, and recognizable characters as rights-sensitive. Use original creative unless the user provides clear rights or source material.
- For AI-generated video, avoid prompts that request copyrighted characters, celebrity likenesses, brand logos, private individuals, or misleading real-world events.
- For AI-generated video, do not request voiceover, dialogue, sound effects, readable text, captions, UI screens, phones displaying text, labels, logos, or signage. Generate clean footage with upbeat music only and provide overlay copy separately.
- Include disclosure guidance when a post uses synthetic media in a context where viewers could reasonably mistake it for real footage.
- Preserve the user's brand voice when provided; otherwise default to concise, concrete, low-hype copy.
- Do not repeat an existing project post topic unless the user explicitly asks for a variation.

## Output Shape

For content-only requests, return:

- `Project`
- `Format`
- `Topic Fingerprint`
- `Duplicate Check`
- `Caption`
- `CTA`
- `Hashtags`
- `Visual Direction`
- `Overlay Text`
- `Alt Text`
- `Notes / Assumptions`

For publishing requests, also return:

- `Buffer Channel`
- `Media URL Requirements`
- `Schedule`
- `Approval Needed`
- `API or Manual Steps`

## References

- Read `references/projects.md` for project state, style guide, post record, and duplicate-check conventions.
- Read `references/buffer.md` for Buffer authentication, scheduling, media URL, and GraphQL mutation guidance.
- Read `references/veo-video.md` when generating or briefing a Veo 3.1 video asset.
- Use `scripts/project_state.py` to initialize projects, inspect history, check duplicates, and save post records.
- Use `scripts/overlay_text.py` to add timed overlay text to local MP4 videos before upload.
