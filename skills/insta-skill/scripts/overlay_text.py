#!/usr/bin/env python3
"""Add timed text overlays to an MP4 using PNG frames and ffmpeg overlay."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


FONT_CANDIDATES = [
    "/System/Library/Fonts/Inter.ttc",
    "/System/Library/Fonts/Supplemental/Inter.ttc",
    "/Library/Fonts/Inter.ttf",
    "/Library/Fonts/Inter.ttc",
    "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
]

DEFAULT_ACCENT = (22, 163, 74, 255)
DEFAULT_TEXT = (17, 24, 39, 255)
DEFAULT_CARD = (255, 255, 255, 224)
DEFAULT_SHADOW = (17, 24, 39, 44)


def find_font(explicit: str | None) -> str:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise SystemExit(f"Font not found: {explicit}")
        return str(path)

    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return candidate

    raise SystemExit("No default font found. Pass --font /path/to/font.ttf")


def load_overlays(path: Path) -> list[dict[str, object]]:
    try:
        overlays = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid overlay JSON: {exc}") from exc

    if not isinstance(overlays, list) or not overlays:
        raise SystemExit("Overlay JSON must be a non-empty list")

    for index, item in enumerate(overlays):
        if not isinstance(item, dict):
            raise SystemExit(f"Overlay {index} must be an object")
        for key in ("start", "end", "text"):
            if key not in item:
                raise SystemExit(f"Overlay {index} missing {key}")
        if float(item["end"]) <= float(item["start"]):
            raise SystemExit(f"Overlay {index} end must be after start")
        if not str(item["text"]).strip():
            raise SystemExit(f"Overlay {index} text is empty")

    return overlays


def parse_color(value: str, default: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    value = value.strip()
    if not value:
        return default
    if value.startswith("#"):
        raw = value[1:]
        if len(raw) == 6:
            return tuple(int(raw[index : index + 2], 16) for index in (0, 2, 4)) + (255,)
        if len(raw) == 8:
            return tuple(int(raw[index : index + 2], 16) for index in (0, 2, 4, 6))
    raise SystemExit(f"Unsupported color value: {value}. Use #RRGGBB or #RRGGBBAA")


def load_style(path: Path | None) -> dict[str, Any]:
    style: dict[str, Any] = {
        "mode": "card",
        "accent": DEFAULT_ACCENT,
        "text": DEFAULT_TEXT,
        "card": DEFAULT_CARD,
        "shadow": DEFAULT_SHADOW,
        "y_ratio": 0.145,
        "max_width_ratio": 0.78,
        "align": "center",
        "stroke_width_ratio": 0.003,
        "font_size_ratio": 0.050,
        "min_font_size_ratio": 0.034,
    }
    if not path:
        return style
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid style JSON: {exc}") from exc

    color_map = {
        "accent_color": "accent",
        "text_color": "text",
        "card_color": "card",
        "shadow_color": "shadow",
    }
    for source, target in color_map.items():
        if source in data:
            style[target] = parse_color(str(data[source]), style[target])  # type: ignore[arg-type]
    for source, target in {"y_ratio": "y_ratio", "max_width_ratio": "max_width_ratio"}.items():
        if source in data:
            style[target] = float(data[source])
    for source, target in {"font_size_ratio": "font_size_ratio", "min_font_size_ratio": "min_font_size_ratio"}.items():
        if source in data:
            style[target] = float(data[source])
    if "mode" in data:
        mode = str(data["mode"]).lower()
        if mode not in {"card", "text"}:
            raise SystemExit("style mode must be either 'card' or 'text'")
        style["mode"] = mode
    if "align" in data:
        align = str(data["align"]).lower()
        if align not in {"left", "center", "right"}:
            raise SystemExit("style align must be left, center, or right")
        style["align"] = align
    if "stroke_width_ratio" in data:
        style["stroke_width_ratio"] = float(data["stroke_width_ratio"])
    return style


def video_size(path: Path) -> tuple[int, int]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    return int(stream["width"]), int(stream["height"])


def fit_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str,
    max_width: int,
    start_size: int,
    min_size: int,
) -> tuple[ImageFont.FreeTypeFont, list[str], int, int]:
    words = text.split()
    for size in range(start_size, min_size - 1, -2):
        font = ImageFont.truetype(font_path, size)
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            width = draw.textbbox((0, 0), candidate, font=font)[2]
            if width <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)

        if len(lines) <= 2 and all(draw.textbbox((0, 0), line, font=font)[2] <= max_width for line in lines):
            line_heights = [draw.textbbox((0, 0), line, font=font)[3] for line in lines]
            text_width = max(draw.textbbox((0, 0), line, font=font)[2] for line in lines)
            text_height = sum(line_heights) + round(size * 0.28) * (len(lines) - 1)
            return font, lines, text_width, text_height

    font = ImageFont.truetype(font_path, min_size)
    return font, [text], draw.textbbox((0, 0), text, font=font)[2], draw.textbbox((0, 0), text, font=font)[3]


def draw_brand_card(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    text: str,
    font_path: str,
    style: dict[str, Any],
) -> None:
    card_max_width = round(width * float(style["max_width_ratio"]))
    pad_x = round(width * 0.038)
    pad_y = round(height * 0.014)
    accent_height = max(4, round(height * 0.005))
    text_max_width = card_max_width - pad_x * 2
    start_size = max(30, round(height * 0.041))
    min_size = max(22, round(height * 0.030))
    scratch = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    scratch_draw = ImageDraw.Draw(scratch)
    font, lines, text_width, text_height = fit_lines(
        scratch_draw, text, font_path, text_max_width, start_size, min_size
    )

    card_width = min(card_max_width, text_width + pad_x * 2)
    card_height = text_height + pad_y * 2
    card_x = round((width - card_width) / 2)
    card_y = round(height * float(style["y_ratio"]))
    radius = round(card_height * 0.22)

    shadow_offset = round(height * 0.008)
    draw.rounded_rectangle(
        (card_x, card_y + shadow_offset, card_x + card_width, card_y + card_height + shadow_offset),
        radius=radius,
        fill=style["shadow"],  # type: ignore[arg-type]
    )
    draw.rounded_rectangle(
        (card_x, card_y, card_x + card_width, card_y + card_height),
        radius=radius,
        fill=style["card"],  # type: ignore[arg-type]
    )
    accent_y = card_y + card_height - accent_height
    draw.rounded_rectangle(
        (card_x + pad_x, accent_y, card_x + card_width - pad_x, accent_y + accent_height),
        radius=round(accent_height / 2),
        fill=style["accent"],  # type: ignore[arg-type]
    )

    line_gap = round(font.size * 0.28)
    current_y = card_y + round((card_height - text_height) / 2)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_height = bbox[3] - bbox[1]
        text_x = round((width - (bbox[2] - bbox[0])) / 2)
        draw.text((text_x, current_y - bbox[1]), line, font=font, fill=style["text"])  # type: ignore[arg-type]
        current_y += line_height + line_gap


def draw_simple_text(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    text: str,
    font_path: str,
    style: dict[str, Any],
) -> None:
    max_width = round(width * float(style["max_width_ratio"]))
    start_size = max(30, round(height * float(style["font_size_ratio"])))
    min_size = max(22, round(height * float(style["min_font_size_ratio"])))
    scratch = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    scratch_draw = ImageDraw.Draw(scratch)
    font, lines, text_width, text_height = fit_lines(scratch_draw, text, font_path, max_width, start_size, min_size)

    margin_x = round(width * 0.075)
    align = str(style["align"])
    if align == "left":
        text_x = margin_x
    elif align == "right":
        text_x = width - margin_x - text_width
    else:
        text_x = round((width - text_width) / 2)

    y = round(height * float(style["y_ratio"]))
    line_gap = round(font.size * 0.22)
    stroke_width = max(1, round(height * float(style["stroke_width_ratio"])))
    shadow_offset = max(2, round(height * 0.004))

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
        line_width = bbox[2] - bbox[0]
        if align == "left":
            current_x = text_x
        elif align == "right":
            current_x = width - margin_x - line_width
        else:
            current_x = round((width - line_width) / 2)

        draw.text(
            (current_x + shadow_offset, y - bbox[1] + shadow_offset),
            line,
            font=font,
            fill=style["shadow"],
            stroke_width=stroke_width,
            stroke_fill=style["shadow"],
        )
        draw.text(
            (current_x, y - bbox[1]),
            line,
            font=font,
            fill=style["text"],
            stroke_width=stroke_width,
            stroke_fill=style["shadow"],
        )
        y += (bbox[3] - bbox[1]) + line_gap


def render_card(
    width: int,
    height: int,
    text: str,
    font_path: str,
    style: dict[str, Any],
) -> Image.Image:
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if style["mode"] == "text":
        draw_simple_text(draw, width, height, text, font_path, style)
    else:
        draw_brand_card(draw, width, height, text, font_path, style)
    return image


def render_animated_sequences(
    overlays: list[dict[str, object]],
    font_path: str,
    width: int,
    height: int,
    directory: Path,
    style: dict[str, Any],
) -> list[Path]:
    sequence_dirs = []
    fps = 24
    slide = round(height * 0.024)

    for index, item in enumerate(overlays, start=1):
        start = float(item["start"])
        end = float(item["end"])
        duration = end - start
        fade = min(0.22, max(0.08, duration * 0.18))
        frame_count = max(2, round(duration * fps))
        base = render_card(width, height, str(item["text"]), font_path, style)
        sequence_dir = directory / f"overlay-{index:02d}"
        sequence_dir.mkdir()

        for frame in range(frame_count):
            t = frame / fps
            if t < fade:
                progress = t / fade
                alpha = progress
                y_offset = round(slide * (1 - progress))
            elif t > duration - fade:
                progress = (duration - t) / fade
                alpha = max(0.0, progress)
                y_offset = -round(slide * (1 - alpha))
            else:
                alpha = 1.0
                y_offset = 0

            canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            frame_image = base.copy()
            if alpha < 1.0:
                r, g, b, a = frame_image.split()
                a = a.point(lambda value: round(value * alpha))
                frame_image.putalpha(a)
            canvas.alpha_composite(frame_image, (0, y_offset))
            canvas.save(sequence_dir / f"frame-{frame + 1:04d}.png")

        sequence_dirs.append(sequence_dir)

    return sequence_dirs


def build_filter(overlays: list[dict[str, object]]) -> str:
    chains = []
    previous = "[0:v]"
    for index, item in enumerate(overlays, start=1):
        start = float(item["start"])
        end = float(item["end"])
        output = f"[v{index}]"
        chains.append(
            f"[{index}:v]setpts=PTS+{start:.3f}/TB[ov{index}];"
            f"{previous}[ov{index}]overlay=0:0:enable='between(t,{start:.3f},{end:.3f})'{output}"
        )
        previous = output
    return ";".join(chains), previous


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("overlays", type=Path)
    parser.add_argument("--font", help="Path to a .ttf/.otf font")
    parser.add_argument("--style-json", type=Path, help="Optional overlay style JSON with colors and layout ratios")
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required but was not found on PATH")
    if not args.input.exists():
        raise SystemExit(f"Input video not found: {args.input}")

    font = find_font(args.font)
    overlays = load_overlays(args.overlays)
    style = load_style(args.style_json)
    width, height = video_size(args.input)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="instagram-overlays-") as tmp:
        sequences = render_animated_sequences(overlays, font, width, height, Path(tmp), style)
        filter_complex, mapped_video = build_filter(overlays)
        command = ["ffmpeg", "-y", "-i", str(args.input)]
        for sequence in sequences:
            command.extend(["-framerate", "24", "-i", str(sequence / "frame-%04d.png")])
        command.extend(
            [
                "-filter_complex",
                filter_complex,
                "-map",
                mapped_video,
                "-map",
                "0:a?",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-c:a",
                "copy",
                "-movflags",
                "+faststart",
                str(args.output),
            ]
        )
        subprocess.run(command, check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
