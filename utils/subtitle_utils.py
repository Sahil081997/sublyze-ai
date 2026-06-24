import os
import srt
import subprocess
import uuid
from datetime import timedelta


def generate_srt(chunks):
    """Convert Whisper timestamp chunks to SRT format.

    Filters out chunks with missing, zero-length, or invalid timestamps so the
    resulting SRT file is always well-formed and compatible with FFmpeg/libass.
    """
    subtitles = []
    idx = 1
    for chunk in chunks:
        ts = chunk.get('timestamp', (None, None))
        start_ts, end_ts = ts[0], ts[1]
        if start_ts is None or end_ts is None:
            continue
        text = chunk.get('text', '').strip()
        if not text:
            continue
        # Guard against zero-length segments
        end_ts = max(float(end_ts), float(start_ts) + 0.5)
        subtitles.append(srt.Subtitle(
            index=idx,
            start=timedelta(seconds=float(start_ts)),
            end=timedelta(seconds=end_ts),
            content=text,
        ))
        idx += 1
    return srt.compose(subtitles)


def save_srt(srt_text, output_path="output_subtitles.srt"):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_text)
    return output_path


def _hex_to_ass_primary(hex_color):
    """Convert #RRGGBB to ASS primary colour &H00BBGGRR."""
    h = (hex_color or "#FFFFFF").lstrip('#')
    h = h.ljust(6, '0')[:6]
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"&H00{b:02X}{g:02X}{r:02X}"


def _hex_to_ass_back(hex_color, opacity):
    """Convert #RRGGBB + opacity (0–1) to ASS back colour &HAABBGGRR."""
    h = (hex_color or "#000000").lstrip('#')
    h = h.ljust(6, '0')[:6]
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    alpha = max(0, min(255, int((1.0 - float(opacity)) * 255)))
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"


def burn_subtitles_to_video(
    video_path, chunks,
    fontsize=24, color="#FFFFFF",
    bg_color="#000000", bg_opacity=0.6,
    session_id=None,
):
    """Burn subtitles into a video using FFmpeg's native subtitles filter (libass).

    This replaces the old MoviePy + PIL approach, which was:
      • Slow   — PIL renders every frame in Python
      • Brittle — hardcoded Linux font path, NoneType crash on bg_color=None
      • Wrong  — shared 'burned_output.mp4' path caused race conditions

    The FFmpeg subtitles filter is battle-tested, GPU-friendly, and handles all
    edge cases (wrapping, unicode, RTL) natively via libass.

    Pipeline:
      1. Write chunks → temporary per-session SRT file
      2. Build ASS force_style string from hex colours + opacity
      3. Run: ffmpeg -vf subtitles='file.srt':force_style='...' -c:v libx264 ...
      4. Return path to the per-session burned MP4

    Args:
        video_path:  Absolute path to the source video.
        chunks:      List of {'timestamp': (start, end), 'text': str} from Whisper.
        fontsize:    Subtitle font size (display points).
        color:       Hex string for text colour, e.g. '#FFFFFF'.
        bg_color:    Hex string for background box, e.g. '#000000'.
        bg_opacity:  Float 0–1 for background opacity (0 = transparent).
        session_id:  Short string used to name temp/output files uniquely.

    Returns:
        Absolute path to the burned MP4 file.

    Raises:
        RuntimeError: If FFmpeg exits non-zero.
    """
    if session_id is None:
        session_id = uuid.uuid4().hex[:12]

    os.makedirs("data", exist_ok=True)

    srt_text = generate_srt(chunks)
    srt_path = os.path.abspath(os.path.join("data", f"subs_{session_id}.srt"))
    output_path = os.path.abspath(os.path.join("data", f"burned_{session_id}.mp4"))
    save_srt(srt_text, srt_path)

    primary = _hex_to_ass_primary(color)
    back    = _hex_to_ass_back(bg_color, bg_opacity)

    # libass uses PlayResY=288 as the virtual canvas height for SRT files.
    # Actual rendered pixel height = (Fontsize / 288) * video_height.
    # For TV/Netflix-style subtitles (~38px at 1080p): Fontsize = 38*288/1080 ≈ 10.
    # We map the user's slider (default 18) through a 0.55 factor to land near that.
    ass_fontsize = max(6, round(fontsize * 0.55))

    # BorderStyle=4 → opaque background box   Alignment=2 → bottom-centre
    # MarginV=10 → ~37px above bottom edge at 1080p (TV/Netflix positioning)
    force_style = (
        f"Fontsize={ass_fontsize},"
        f"PrimaryColour={primary},"
        f"BackColour={back},"
        f"BorderStyle=4,"
        f"Outline=0,Shadow=0,"
        f"Alignment=2,"
        f"MarginV=10"
    )

    # Escape the SRT path for FFmpeg's subtitles filter:
    # backslashes → forward slashes, then escape any remaining colons
    srt_filter_path = srt_path.replace('\\', '/').replace(':', '\\:')

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
            f"stderr (last 2 000 chars):\n{result.stderr[-2000:]}"
        )

    return output_path
