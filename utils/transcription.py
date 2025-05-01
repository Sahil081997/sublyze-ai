from transformers import pipeline
import torch
import streamlit as st


# Load Whisper model only once (small for now, can be upgraded to medium/large later)
@st.cache_resource
def load_whisper_model():
    device = 0 if torch.cuda.is_available() else -1
    return pipeline("automatic-speech-recognition", model="openai/whisper-small", device=device)

# Run inference on extracted audio
def transcribe_audio(audio_path):
    model = load_whisper_model()
    result = model(audio_path, return_timestamps=True)
    return result["text"], result.get("chunks", [])  # 'chunks' contains word-level timestamps