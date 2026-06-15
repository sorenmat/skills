# Project State Reference

Insta Skill keeps reusable project state outside the repository under:

```text
~/.local/insta-skill/<project>/
```

Use `INSTA_SKILL_HOME` to override the base directory for tests or temporary runs.

## Project Names

Resolve a project from the user request:

- Domain or URL: normalize to the registrable-looking host, e.g. `https://nemmad.com` becomes `nemmad.com`.
- Brand or account name: lowercase, replace unsupported characters with `-`, and keep it stable between runs.
- Do not include protocol, paths, query strings, or secrets in the project slug.

## Directory Layout

Each project directory contains:

```text
project.json
style.md
posts/
  <post-id>.json
  <post-id>.md
```

`project.json` is machine-readable project metadata. `style.md` is the human-editable content and creative guide. `posts/*.json` are durable records used to avoid repeats and continue work. `posts/*.md` are readable snapshots for quick review.

Do not store API keys, OAuth tokens, private Buffer profile IDs, signed media URLs, or temporary provider download URLs in project files. Store local asset paths and stable public media URLs only when they are safe to keep.

## Commands

Initialize or inspect a project:

```bash
python3 skills/insta-skill/scripts/project_state.py init nemmad.com
python3 skills/insta-skill/scripts/project_state.py list-posts nemmad.com
```

Check whether a topic has already been used:

```bash
python3 skills/insta-skill/scripts/project_state.py check-duplicate nemmad.com "last minute dinner planning for busy families"
```

Save a post record from a JSON file:

```bash
python3 skills/insta-skill/scripts/project_state.py save-post nemmad.com post.json
```

Or from stdin:

```bash
python3 skills/insta-skill/scripts/project_state.py save-post nemmad.com -
```

All commands print JSON to stdout and exit `0` for normal outcomes, including duplicate findings. Read the `duplicate` boolean rather than relying on a non-zero exit code.

## Post JSON

Use this shape when saving records. Extra fields are preserved.

```json
{
  "status": "drafted",
  "format": "reel",
  "topic_fingerprint": "last-minute dinner planning for busy families",
  "hook": "Hvad skal vi spise i aften?",
  "caption": "Kort, konkret Instagram-tekst...",
  "cta": "Prøv NemMad gratis",
  "hashtags": {
    "branded": ["#NemMad"],
    "niche": ["#madplan", "#aftensmad"],
    "discovery": ["#hverdagsmad"]
  },
  "overlay_text": [
    {"start": 0.2, "end": 1.2, "text": "Hvad skal vi spise?"},
    {"start": 1.4, "end": 2.6, "text": "Lav en madplan"}
  ],
  "visual_direction": "Vertical 6 second kitchen transformation video...",
  "assets": {
    "video_local_path": "/tmp/nemmad-reel.mp4",
    "video_public_url": ""
  },
  "buffer": {
    "status": "",
    "update_id": "",
    "channel_id": ""
  },
  "notes": "Assumptions and review notes."
}
```

Valid status values:

- `idea`
- `drafted`
- `rendered`
- `buffer_draft`
- `scheduled`
- `published`
- `rejected`

## Duplicate Checks

Create `topic_fingerprint` from the core idea, not from the exact caption. Include:

- Audience.
- Problem or desire.
- Product value.
- Seasonal or campaign angle, if relevant.

The helper normalizes fingerprints by lowercasing, removing punctuation, and collapsing whitespace. Treat a duplicate as a stop sign unless the user explicitly asks for a variation. If creating a variation, save a distinct fingerprint that names the new angle.

## Bootstrapping

`init` creates a generic style guide from the project name and, when the input is a URL or domain, best-effort website metadata such as title, description, language, and Open Graph fields.

For `nemmad.com`, the default `style.md` also includes the project-specific rules defined during this workflow:

- Danish copy with correct characters: `å`, `æ`, and `ø`.
- Practical, direct, low-hype tone.
- Instagram Reels default to 6 seconds, vertical `9:16`, `veo-3.1-generate-preview`, and `720p` unless quality needs justify more.
- Video prompts must be written as time-coded generation scripts with exact second ranges, lighting, camera, music, and negative prompts.
- Recipe/process videos should use 8 seconds when the story needs multiple steps.
- No voiceover, dialogue, sound effects, ambience, readable generated text, UI screens, mobile phones showing text, labels, logos, or signage in generated video.
- Ask for upbeat instrumental music only.
- Add marketing text afterwards with programmatic overlays.
- Overlay style: compact white rounded card, dark text, green accent, subtle shadow, quick fade/slide animation.

## Workflow Discipline

Before generating a new post:

1. Run `init` if the project directory does not exist.
2. Read `style.md`.
3. Run `list-posts` and scan recent records.
4. Create and check `topic_fingerprint`.
5. Save the result once the draft, rendered asset, Buffer draft, schedule, or published state exists.
