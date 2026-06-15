#!/usr/bin/env python3
"""Manage persistent project state for insta-skill."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


DEFAULT_HOME = Path("~/.local/insta-skill").expanduser()
VALID_STATUSES = {
    "idea",
    "drafted",
    "rendered",
    "buffer_draft",
    "scheduled",
    "published",
    "rejected",
}


class MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.in_title = False
        self.meta: dict[str, str] = {}
        self.links: dict[str, str] = {}
        self.html_lang = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key.lower(): value or "" for key, value in attrs}
        if tag == "html":
            self.html_lang = attr.get("lang", self.html_lang)
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            key = attr.get("property") or attr.get("name")
            content = attr.get("content")
            if key and content:
                self.meta[key.lower()] = html.unescape(content.strip())
        elif tag == "link":
            rel = attr.get("rel", "").lower()
            href = attr.get("href")
            if rel and href:
                self.links[rel] = html.unescape(href.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_home(args: argparse.Namespace) -> Path:
    raw = args.home or os.environ.get("INSTA_SKILL_HOME")
    return Path(raw).expanduser() if raw else DEFAULT_HOME


def slugify(value: str, allow_dot: bool = False) -> str:
    allowed = r"[^a-z0-9.]+" if allow_dot else r"[^a-z0-9]+"
    slug = re.sub(allowed, "-", value.lower()).strip("-.")
    return slug or "project"


def normalize_source(project: str) -> tuple[str, str, str]:
    candidate = project.strip()
    if not candidate:
        raise SystemExit("Project name is required")

    has_scheme = bool(urllib.parse.urlparse(candidate).scheme)
    looks_like_domain = "." in candidate and " " not in candidate

    if has_scheme or looks_like_domain:
        url = candidate if has_scheme else f"https://{candidate}"
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or candidate).lower()
        host = host[4:] if host.startswith("www.") else host
        netloc = host
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        source_url = urllib.parse.urlunparse((parsed.scheme or "https", netloc, "", "", "", ""))
        return slugify(host, allow_dot=True), "url", source_url

    return slugify(candidate, allow_dot=False), "name", ""


def normalize_fingerprint(value: str) -> str:
    value = html.unescape(value).lower()
    value = re.sub(r"https?://\S+", " ", value)
    value = re.sub(r"[^a-z0-9æøåäöüéèáàíìóòúùñç]+", " ", value, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", value).strip()


def post_id_from(data: dict[str, Any]) -> str:
    if data.get("id"):
        return slugify(str(data["id"]), allow_dot=False)
    source = " ".join(
        str(data.get(key, ""))
        for key in ("topic_fingerprint", "hook", "caption", "visual_direction")
        if data.get(key)
    ).strip()
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:8] if source else "untitled"
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%d-%H%M%S")
    label_source = data.get("hook") or data.get("topic_fingerprint") or digest
    return f"{timestamp}-{slugify(str(label_source), allow_dot=False)[:48]}-{digest}".strip("-")


def fetch_metadata(source_url: str) -> dict[str, str]:
    if not source_url:
        return {}
    request = urllib.request.Request(
        source_url,
        headers={
            "User-Agent": "insta-skill/1.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            content_type = response.headers.get("content-type", "")
            charset = response.headers.get_content_charset() or "utf-8"
            raw = response.read(750_000)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"fetch_error": str(exc)}

    if "html" not in content_type and content_type:
        return {"fetch_error": f"Expected HTML, got {content_type}"}

    parser = MetadataParser()
    parser.feed(raw.decode(charset, errors="replace"))
    title = " ".join(" ".join(parser.title_parts).split())
    return {
        "title": parser.meta.get("og:title") or title,
        "description": parser.meta.get("description") or parser.meta.get("og:description") or "",
        "keywords": parser.meta.get("keywords", ""),
        "language": parser.html_lang or parser.meta.get("og:locale", ""),
        "image": parser.meta.get("og:image", ""),
        "canonical": parser.links.get("canonical", ""),
    }


def project_dir(home: Path, project: str) -> tuple[Path, str, str, str]:
    slug, source_type, source_url = normalize_source(project)
    return home / slug, slug, source_type, source_url


def nemmad_style(metadata: dict[str, str]) -> str:
    title = metadata.get("title") or "NemMad"
    description = metadata.get("description") or "Madplaner, opskrifter og indkøb gjort nemmere."
    return f"""# Style Guide: nemmad.com

## Brand Snapshot

- Project: NemMad
- Website title: {title}
- Website description: {description}
- Language: Danish (`da-DK`)
- Core promise: make weekly dinner planning and grocery decisions feel simpler, calmer, and more appetizing.

## Voice

- Write in Danish with correct characters: `å`, `æ`, and `ø`.
- Be practical, direct, warm, and low-hype.
- Favor everyday kitchen language over startup jargon.
- Use specific dinner-planning moments: "Hvad skal vi spise?", madplan, indkøbsliste, hverdagsmad, travle hverdage.
- Avoid vague AI claims unless the post directly supports them.

## Instagram Content

- Default format: Reel.
- Default model: `veo-3.1-generate-preview`.
- Duration: 6 seconds.
- Aspect ratio: vertical `9:16`.
- Resolution: `720p` for drafts unless quality needs justify `1080p`.
- Video should feel active: quick cuts, overhead prep, ingredients moving into order, plated meal finish.
- Write video prompts as time-coded generation scripts with exact second ranges, lighting, camera, music, and negative prompts.
- Use 8 seconds for recipe/process videos that need multiple steps.
- No voiceover, dialogue, sound effects, ambience, readable generated text, UI screens, mobile phones showing text, labels, logos, or signage.
- Ask for upbeat instrumental music only.
- Add all marketing copy programmatically as overlay text after video generation.

## Visual Direction

- Modern Scandinavian home kitchen.
- Warm practical light, fresh ingredients, organized groceries, appetizing everyday dinners.
- Show transformation from decision fatigue or messy planning to a simple meal-plan outcome.
- Keep the last second visually clean enough for a CTA overlay.
- Avoid faces unless the user provides source material and approves it.

## Overlay Style

- Compact white rounded card.
- Dark navy text.
- Green accent line or dot.
- Subtle shadow.
- Quick fade/slide animation; no static giant badge.
- Keep snippets short, usually 2-5 words.

## Useful Overlay Progressions

```text
0.2-1.2s: Hvad skal vi spise?
1.4-2.6s: Lav en madplan
2.8-4.2s: Få indkøbslisten
4.6-5.8s: Prøv NemMad gratis
```

```text
0.2-1.1s: Aftensmad uden stress
1.3-2.5s: Ugen planlagt
2.7-4.1s: Indkøb samlet
4.5-5.8s: Prøv NemMad gratis
```

## CTA Options

- Prøv NemMad gratis
- Lav din madplan
- Gør hverdagsmaden lettere
"""


def generic_style(slug: str, source_url: str, metadata: dict[str, str]) -> str:
    title = metadata.get("title") or slug
    description = metadata.get("description") or "Add a concise brand description here."
    language = metadata.get("language") or "Add preferred language/locale here."
    return f"""# Style Guide: {slug}

## Brand Snapshot

- Project: {slug}
- Source URL: {source_url or "Not set"}
- Website title: {title}
- Website description: {description}
- Language: {language}

## Voice

- Define the brand voice before publishing: tone, vocabulary, words to avoid, and required language.
- Keep Instagram copy concrete and useful.
- Do not invent claims, prices, availability, reviews, partnerships, or metrics.

## Instagram Defaults

- Default format: Reel when motion strengthens the idea; otherwise feed image or carousel.
- Default video model: `veo-3.1-generate-preview`.
- Duration: 6 seconds.
- Aspect ratio: vertical `9:16`.
- Resolution: `720p` for drafts unless quality needs justify more.
- Write video prompts as time-coded generation scripts with exact second ranges, lighting, camera, music, and negative prompts.
- Use 8 seconds for recipe/process videos that need multiple steps.
- No voiceover, dialogue, sound effects, ambience, readable generated text, UI screens, phones showing text, labels, logos, or signage unless explicitly approved.
- Ask for upbeat instrumental music only.
- Add all marketing copy programmatically as overlay text after video generation.

## Visual Direction

- Define the visual world: setting, lighting, colors, subject matter, camera movement, and what must never appear.
- Keep important action away from top and bottom Instagram UI-safe areas.

## Overlay Style

- Define card shape, colors, typography, placement, and animation.
- Keep snippets short, usually 2-5 words.

## CTA Options

- Add approved calls to action here.
"""


def init_project(args: argparse.Namespace) -> None:
    home = resolve_home(args)
    directory, slug, source_type, source_url = project_dir(home, args.project)
    posts_dir = directory / "posts"
    metadata = fetch_metadata(source_url)
    created = False

    directory.mkdir(parents=True, exist_ok=True)
    posts_dir.mkdir(exist_ok=True)

    project_path = directory / "project.json"
    now = utc_now()
    if project_path.exists():
        data = json.loads(project_path.read_text(encoding="utf-8"))
        data["updated_at"] = now
        data.setdefault("created_at", now)
    else:
        created = True
        data = {
            "slug": slug,
            "source": args.project,
            "source_type": source_type,
            "source_url": source_url,
            "created_at": now,
            "updated_at": now,
            "statuses": sorted(VALID_STATUSES),
        }

    clean_metadata = {key: value for key, value in metadata.items() if value and key != "fetch_error"}
    if clean_metadata:
        data["metadata"] = clean_metadata
    else:
        data.setdefault("metadata", {})
    if metadata.get("fetch_error"):
        data["last_metadata_fetch_error"] = metadata["fetch_error"]
    project_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    style_path = directory / "style.md"
    if not style_path.exists():
        style = nemmad_style(metadata) if slug == "nemmad.com" else generic_style(slug, source_url, metadata)
        style_path.write_text(style, encoding="utf-8")

    print_json(
        {
            "project": slug,
            "created": created,
            "path": str(directory),
            "style_path": str(style_path),
            "posts_path": str(posts_dir),
            "metadata": data.get("metadata", {}),
        }
    )


def load_posts(directory: Path) -> list[dict[str, Any]]:
    posts = []
    for path in sorted((directory / "posts").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        data["_path"] = str(path)
        posts.append(data)
    return posts


def list_posts(args: argparse.Namespace) -> None:
    directory, slug, _, _ = project_dir(resolve_home(args), args.project)
    posts = load_posts(directory) if directory.exists() else []
    summary = [
        {
            "id": post.get("id"),
            "status": post.get("status"),
            "format": post.get("format"),
            "topic_fingerprint": post.get("topic_fingerprint"),
            "created_at": post.get("created_at"),
            "updated_at": post.get("updated_at"),
            "path": post.get("_path"),
        }
        for post in sorted(posts, key=lambda item: str(item.get("created_at", "")), reverse=True)
    ]
    print_json({"project": slug, "count": len(summary), "posts": summary})


def check_duplicate(args: argparse.Namespace) -> None:
    directory, slug, _, _ = project_dir(resolve_home(args), args.project)
    needle = normalize_fingerprint(args.topic_fingerprint)
    matches = []
    for post in load_posts(directory) if directory.exists() else []:
        normalized = post.get("topic_fingerprint_normalized") or normalize_fingerprint(
            str(post.get("topic_fingerprint", ""))
        )
        if normalized and normalized == needle:
            matches.append(
                {
                    "id": post.get("id"),
                    "status": post.get("status"),
                    "topic_fingerprint": post.get("topic_fingerprint"),
                    "path": post.get("_path"),
                }
            )
    print_json({"project": slug, "duplicate": bool(matches), "matches": matches})


def read_post_json(value: str) -> dict[str, Any]:
    raw = sys.stdin.read() if value == "-" else Path(value).read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid post JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Post JSON must be an object")
    return data


def save_post(args: argparse.Namespace) -> None:
    directory, slug, _, _ = project_dir(resolve_home(args), args.project)
    if not directory.exists():
        raise SystemExit(f"Project does not exist. Run init first: {slug}")
    posts_dir = directory / "posts"
    posts_dir.mkdir(exist_ok=True)

    data = read_post_json(args.post_json)
    now = utc_now()
    data.setdefault("created_at", now)
    data["updated_at"] = now
    data.setdefault("status", "drafted")
    if data["status"] not in VALID_STATUSES:
        raise SystemExit(f"Invalid status: {data['status']}. Expected one of: {', '.join(sorted(VALID_STATUSES))}")
    if not data.get("topic_fingerprint"):
        data["topic_fingerprint"] = " ".join(
            str(data.get(key, "")) for key in ("hook", "caption", "visual_direction") if data.get(key)
        ).strip()
    if not data["topic_fingerprint"]:
        raise SystemExit("Post JSON needs topic_fingerprint or enough hook/caption/visual_direction to derive one")

    data["topic_fingerprint_normalized"] = normalize_fingerprint(str(data["topic_fingerprint"]))
    data["id"] = post_id_from(data)

    json_path = posts_dir / f"{data['id']}.json"
    md_path = posts_dir / f"{data['id']}.md"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(data), encoding="utf-8")

    print_json({"project": slug, "id": data["id"], "json_path": str(json_path), "markdown_path": str(md_path)})


def render_markdown(data: dict[str, Any]) -> str:
    hashtags = data.get("hashtags", "")
    if isinstance(hashtags, dict):
        hashtag_text = "\n".join(
            f"- {group}: {' '.join(values) if isinstance(values, list) else values}"
            for group, values in hashtags.items()
        )
    elif isinstance(hashtags, list):
        hashtag_text = " ".join(str(item) for item in hashtags)
    else:
        hashtag_text = str(hashtags)

    overlay = data.get("overlay_text", "")
    overlay_text = json.dumps(overlay, ensure_ascii=False, indent=2) if overlay else ""
    assets = json.dumps(data.get("assets", {}), ensure_ascii=False, indent=2)
    buffer = json.dumps(data.get("buffer", {}), ensure_ascii=False, indent=2)

    return f"""# {data.get("hook") or data.get("topic_fingerprint") or data.get("id")}

- Status: {data.get("status")}
- Format: {data.get("format", "")}
- Topic fingerprint: {data.get("topic_fingerprint")}
- Created: {data.get("created_at")}
- Updated: {data.get("updated_at")}

## Caption

{data.get("caption", "")}

## CTA

{data.get("cta", "")}

## Hashtags

{hashtag_text}

## Visual Direction

{data.get("visual_direction", "")}

## Overlay Text

```json
{overlay_text}
```

## Alt Text

{data.get("alt_text", "")}

## Assets

```json
{assets}
```

## Buffer

```json
{buffer}
```

## Notes

{data.get("notes", "")}
"""


def print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", help="Override state base directory. Defaults to INSTA_SKILL_HOME or ~/.local/insta-skill.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create or update a project directory")
    init.add_argument("project")
    init.set_defaults(func=init_project)

    list_cmd = subparsers.add_parser("list-posts", help="List saved post records")
    list_cmd.add_argument("project")
    list_cmd.set_defaults(func=list_posts)

    duplicate = subparsers.add_parser("check-duplicate", help="Check a normalized topic fingerprint")
    duplicate.add_argument("project")
    duplicate.add_argument("topic_fingerprint")
    duplicate.set_defaults(func=check_duplicate)

    save = subparsers.add_parser("save-post", help="Save a post record from a JSON path or stdin")
    save.add_argument("project")
    save.add_argument("post_json")
    save.set_defaults(func=save_post)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
