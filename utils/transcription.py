import streamlit as st
import whisper


@st.cache_resource(show_spinner=False)
def load_whisper_model():
    """Load Whisper-small once and cache it across all sessions.

    Uses the openai-whisper package which downloads from Azure CDN
    (openaipublic.azureedge.net) — no HuggingFace Hub required.
    Model is cached to ~/.cache/whisper after first download.
    """
    return whisper.load_model("small")


def transcribe_audio(audio_path):
    """Transcribe an audio file with Whisper and return segment-level chunks.

    openai-whisper returns segments with guaranteed start/end timestamps —
    no None values, no zero-length segments — so no extra validation needed.

    Returns:
        transcript (str): Full concatenated transcript text.
        chunks (list[dict]): Each item is {'timestamp': (float, float), 'text': str}.
    """
    model = load_whisper_model()
    result = model.transcribe(audio_path, verbose=False)

    transcript = result.get("text", "").strip()
    segments   = result.get("segments", [])

    chunks = []
    for seg in segments:
        start = float(seg.get("start", 0.0))
        end   = float(seg.get("end",   start + 1.0))
        text  = seg.get("text", "").strip()
        if not text:
            continue
        chunks.append({"timestamp": (start, end), "text": text})

    return transcript, chunks