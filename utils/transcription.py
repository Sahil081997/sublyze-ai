import streamlit as st
import torch
from transformers import pipeline


@st.cache_resource(show_spinner=False)
def load_whisper_model():
    """Load Whisper-small once and cache it across all sessions.

    Uses GPU when available; falls back to CPU automatically.
    chunk_length_s=30 + stride_length_s=5 gives a 5-second overlap between
    30-second windows, which dramatically improves accuracy on longer videos
    by reducing boundary-cut transcription errors.
    """
    device = 0 if torch.cuda.is_available() else -1
    return pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-small",
        device=device,
        chunk_length_s=30,
        stride_length_s=5,
    )


def transcribe_audio(audio_path):
    """Transcribe an audio file with Whisper and return validated chunks.

    Whisper's HuggingFace pipeline sometimes returns chunks where:
      - end timestamp is None (audio cut-off at window boundary)
      - end <= start (zero-length segment)
      - text is empty or whitespace-only

    This function sanitises all such cases so downstream SRT generation
    and FFmpeg burning always receive well-formed input.

    Returns:
        transcript (str): Full concatenated transcript text.
        chunks (list[dict]): Each item is {'timestamp': (float, float), 'text': str}.
    """
    model = load_whisper_model()
    result = model(audio_path, return_timestamps=True)

    transcript = result.get("text", "").strip()
    raw_chunks = result.get("chunks", [])

    validated = []
    for chunk in raw_chunks:
        ts = chunk.get('timestamp', (None, None))
        if ts is None or len(ts) < 2:
            continue
        start, end = ts[0], ts[1]
        if start is None:
            continue
        # Clamp None / zero-length end to start + 1 s
        if end is None or end <= start:
            end = float(start) + 1.0
        text = chunk.get('text', '').strip()
        if not text:
            continue
        validated.append({'timestamp': (float(start), float(end)), 'text': text})

    return transcript, validated