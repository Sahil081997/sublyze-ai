import os
import re
import srt
import subprocess
import uuid
from datetime import timedelta


# ── Preset style definitions ──────────────────────────────────────────────────
PRESET_STYLES = {
    "subtle": {
        "label": "Subtle",   "emoji": "🎬",
        "desc":  "Semi-transparent box — Netflix / YouTube style",
        "font_size": 18, "color": "#FFFFFF",
        "bg_color": "#000000", "bg_opacity": 0.6,
        "border_style": "box", "stroke_color": "#000000", "stroke_width": 0,
        "shadow": 0, "position": "bottom", "text_case": "original",
    },
    "bold": {
        "label": "Bold",     "emoji": "💥",
        "desc":  "TikTok / Shorts — thick stroke, all-caps",
        "font_size": 22, "color": "#FFFFFF",
        "bg_color": "#000000", "bg_opacity": 0.0,
        "border_style": "outline", "stroke_color": "#000000", "stroke_width": 3,
        "shadow": 1, "position": "bottom", "text_case": "upper",
    },
    "cinematic": {
        "label": "Cinematic", "emoji": "🎥",
        "desc":  "Classic film — thin outline, no background",
        "font_size": 18, "color": "#FFFFFF",
        "bg_color": "#000000", "bg_opacity": 0.0,
        "border_style": "outline", "stroke_color": "#000000", "stroke_width": 2,
        "shadow": 2, "position": "bottom", "text_case": "original",
    },
    "neon": {
        "label": "Neon",     "emoji": "✨",
        "desc":  "Bold yellow on dark — social media pop",
        "font_size": 20, "color": "#FFE600",
        "bg_color": "#000000", "bg_opacity": 0.75,
        "border_style": "box", "stroke_color": "#000000", "stroke_width": 0,
        "shadow": 0, "position": "bottom", "text_case": "upper",
    },
    "news": {
        "label": "News",     "emoji": "📰",
        "desc":  "Solid black block — broadcast / news style",
        "font_size": 18, "color": "#FFFFFF",
        "bg_color": "#000000", "bg_opacity": 1.0,
        "border_style": "box", "stroke_color": "#000000", "stroke_width": 0,
        "shadow": 0, "position": "bottom", "text_case": "original",
    },
    "minimal": {
        "label": "Minimal",  "emoji": "🤍",
        "desc":  "Drop shadow only — clean, no background",
        "font_size": 18, "color": "#FFFFFF",
        "bg_color": "#000000", "bg_opacity": 0.0,
        "border_style": "none", "stroke_color": "#000000", "stroke_width": 0,
        "shadow": 3, "position": "bottom", "text_case": "original",
    },
}


# ── Text helpers ──────────────────────────────────────────────────────────────
def _apply_case(text: str, text_case: str) -> str:
    if text_case == "upper":
        return text.upper()
    if text_case == "lower":
        return text.lower()
    return text


def merge_short_segments(chunks, min_duration: float = 2.0, min_words: int = 3):
    """Merge very short Whisper segments into longer, more readable subtitle lines.

    Whisper sometimes produces single-word segments for slow or staccato speech.
    This function combines consecutive segments until each one meets the minimum
    duration AND word-count thresholds, keeping timestamps contiguous.
    """
    if not chunks:
        return chunks

    merged = []
    current = dict(chunks[0])

    for chunk in chunks[1:]:
        dur   = current["timestamp"][1] - current["timestamp"][0]
        words = len(current["text"].split())
        if dur < min_duration or words < min_words:
            current = {
                "timestamp": (current["timestamp"][0], chunk["timestamp"][1]),
                "text":      current["text"].rstrip() + " " + chunk["text"].lstrip(),
            }
        else:
            merged.append(current)
            current = dict(chunk)

    merged.append(current)
    return merged


# ── SRT generation ────────────────────────────────────────────────────────────
def generate_srt(chunks, text_case: str = "original") -> str:
    """Convert Whisper chunks to an SRT string, applying optional text transforms."""
    subtitles = []
    idx = 1
    for chunk in chunks:
        ts = chunk.get("timestamp", (None, None))
        start_ts, end_ts = ts[0], ts[1]
        if start_ts is None or end_ts is None:
            continue
        text = _apply_case(chunk.get("text", "").strip(), text_case)
        if not text:
            continue
        end_ts = max(float(end_ts), float(start_ts) + 0.5)
        subtitles.append(srt.Subtitle(
            index=idx,
            start=timedelta(seconds=float(start_ts)),
            end=timedelta(seconds=end_ts),
            content=text,
        ))
        idx += 1
    return srt.compose(subtitles)


def save_srt(srt_text: str, output_path: str = "output_subtitles.srt") -> str:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_text)
    return output_path


# ── Colour converters for ASS format ─────────────────────────────────────────
def _hex_to_ass_primary(hex_color: str) -> str:
    """#RRGGBB → ASS &H00BBGGRR (fully opaque primary colour)."""
    h = (hex_color or "#FFFFFF").lstrip("#").ljust(6, "0")[:6]
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"&H00{b:02X}{g:02X}{r:02X}"


def _hex_to_ass_back(hex_color: str, opacity: float) -> str:
    """#RRGGBB + opacity (0–1) → ASS &HAABBGGRR back colour."""
    h = (hex_color or "#000000").lstrip("#").ljust(6, "0")[:6]
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    alpha = max(0, min(255, int((1.0 - float(opacity)) * 255)))
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"


# ── Core burn function ────────────────────────────────────────────────────────
def burn_subtitles_to_video(
    video_path: str,
    chunks: list,
    fontsize: int       = 18,
    color: str          = "#FFFFFF",
    bg_color: str       = "#000000",
    bg_opacity: float   = 0.6,
    border_style: str   = "box",      # "box" | "outline" | "none"
    stroke_color: str   = "#000000",
    stroke_width: int   = 0,
    shadow: int         = 0,
    position: str       = "bottom",   # "top" | "center" | "bottom"
    text_case: str      = "original", # "original" | "upper" | "lower"
    session_id: str     = None,
) -> str:
    """Burn subtitles into a video using FFmpeg's native subtitles filter (libass).

    Supports six visual modes via border_style:
      box     — semi/fully opaque coloured rectangle (Netflix/YouTube)
      outline — text stroke with optional drop shadow (TikTok/cinematic)
      none    — drop shadow only, no background (minimalist)

    libass virtual canvas is PlayResY=288, so actual pixel height is:
      pixel_height = (ass_fontsize / 288) * video_height
    The 0.55 factor maps the user-facing slider (default 18) to ~37px at 1080p.
    """
    if session_id is None:
        session_id = uuid.uuid4().hex[:12]

    os.makedirs("data", exist_ok=True)
    srt_text   = generate_srt(chunks, text_case=text_case)
    srt_path   = os.path.abspath(os.path.join("data", f"subs_{session_id}.srt"))
    output_path = os.path.abspath(os.path.join("data", f"burned_{session_id}.mp4"))
    save_srt(srt_text, srt_path)

    primary      = _hex_to_ass_primary(color)
    ass_fontsize = max(6, round(fontsize * 0.55))

    # ── Alignment / position ──────────────────────────────────────────────────
    alignment_map = {"bottom": 2, "center": 5, "top": 8}
    alignment = alignment_map.get(position, 2)
    margin_v  = 10 if position in ("bottom", "top") else 0

    # ── Build force_style string ──────────────────────────────────────────────
    base = (
        f"Fontname=Arial,"
        f"Fontsize={ass_fontsize},"
        f"PrimaryColour={primary},"
        f"Alignment={alignment},"
        f"MarginV={margin_v},"
        f"Bold=-1"
    )

    if border_style == "box":
        back = _hex_to_ass_back(bg_color, bg_opacity)
        style_extra = f"BackColour={back},BorderStyle=3,Outline=0,Shadow=0"
    elif border_style == "outline":
        outline_col = _hex_to_ass_primary(stroke_color)
        clamped_w   = max(0, min(8, int(stroke_width)))
        style_extra = (
            f"OutlineColour={outline_col},"
            f"BorderStyle=1,"
            f"Outline={clamped_w},"
            f"Shadow={max(0, min(5, int(shadow)))}"
        )
    else:  # none
        style_extra = (
            f"BorderStyle=1,"
            f"Outline=0,"
            f"Shadow={max(0, min(5, int(shadow)))}"
        )

    force_style = f"{base},{style_extra}"

    # Escape the SRT path for FFmpeg subtitles filter
    srt_filter_path = srt_path.replace("\\", "/").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"subtitles='{srt_filter_path}':force_style='{force_style}'",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg subtitle burn failed (exit {result.returncode}).\n\n"
            f"{result.stderr[-2000:]}"
        )

    return output_path
