import os
import uuid
import ffmpeg

def save_uploaded_file(uploaded_file, save_dir="data"):
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"{uuid.uuid4()}.mp4")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def extract_audio(video_path, audio_path=None):
    if not audio_path:
        audio_path = video_path.replace(".mp4", ".wav").replace(".mov", ".wav")
    (
        ffmpeg
        .input(video_path)
        .output(audio_path, format='wav', acodec='pcm_s16le', ac=1, ar='16000')
        .overwrite_output()
        .run(quiet=True)
    )
    return audio_path