import os
import uuid
import ffmpeg


def save_uploaded_file(uploaded_file, save_dir="data"):
    """Save an uploaded Streamlit file to disk, preserving its original extension.

    The original code always forced a .mp4 extension, which caused subtle bugs
    when processing .mov files (the audio-path replace logic silently failed).
    """
    os.makedirs(save_dir, exist_ok=True)
    original_ext = os.path.splitext(uploaded_file.name)[-1].lower() or ".mp4"
    file_path = os.path.join(save_dir, f"{uuid.uuid4()}{original_ext}")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def extract_audio(video_path, audio_path=None):
    """Extract mono 16 kHz PCM WAV audio from a video file using FFmpeg.

    Whisper expects exactly this format: mono, 16 kHz, 16-bit PCM WAV.
    Uses os.path.splitext so any video extension (.mp4, .mov, …) works correctly.
    """
    if not audio_path:
        base, _ = os.path.splitext(video_path)
        audio_path = f"{base}.wav"
    (
        ffmpeg
        .input(video_path)
        .output(audio_path, format='wav', acodec='pcm_s16le', ac=1, ar='16000')
        .overwrite_output()
        .run(quiet=True)
    )
    return audio_path


def cleanup_session_files(*paths):
    """Delete temporary per-session files (WAV audio, intermediate SRT).

    Call after the burned video has been confirmed and served, to prevent
    unbounded disk growth on the server.
    """
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass