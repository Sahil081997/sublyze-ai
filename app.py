import streamlit as st
import os
from utils.audio_utils import save_uploaded_file, extract_audio
from utils.transcription import transcribe_audio
from utils.subtitle_utils import generate_srt, save_srt, burn_subtitles_to_video
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch

st.set_page_config(page_title="Sublyze AI", layout="wide")
st.markdown("""
    <style>
    .element-container iframe {
        height: auto !important;
        max-height: 75vh !important;
        max-width: 100% !important;
        object-fit: contain !important;
    }
    video {
        max-height: 75vh !important;
        width: auto !important;
        max-width: 100% !important;
        object-fit: contain !important;
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
""", unsafe_allow_html=True)

SUPPORTED_FORMATS = ["mp4", "mov"]
MAX_FILE_SIZE_MB = 200

if 'video_path' not in st.session_state:
    st.session_state.video_path = None
if 'chunks' not in st.session_state:
    st.session_state.chunks = None
if 'transcript' not in st.session_state:
    st.session_state.transcript = None
if 'burned_video_path' not in st.session_state:
    st.session_state.burned_video_path = None
if 'font_size' not in st.session_state:
    st.session_state.font_size = 16
if 'text_color' not in st.session_state:
    st.session_state.text_color = "#FFFFFF"
if 'bg_color' not in st.session_state:
    st.session_state.bg_color = "#000000"
if 'bg_opacity' not in st.session_state:
    st.session_state.bg_opacity = 0.50
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Edit Subtitles"
if 'steps' not in st.session_state:
    st.session_state.steps = {
        "upload": False,
        "extract": False,
        "transcribe": False,
        "subtitle": False,
        "burn": False
    }
if 'translation_language' not in st.session_state:
    st.session_state.translation_language = None

st.sidebar.title("🎬 Sublyze AI")
page = st.sidebar.radio("Navigation", ["Editor", "Privacy"])

if page == "Privacy":
    st.title("🔐 Privacy Policy")
    st.markdown("""
    <div style='text-align: center; margin-top: 40px;'>
        <h2 style='font-weight: bold;'>tl;dr, It's free and private.</h2>
        <p style='font-size: 18px;'>The entire transcription and subtitling process is done <strong>locally in your browser</strong>.<br>
        Your video, subtitles, or any other data will <strong>never be sent to any server</strong>.</p>
        <p style='font-size: 18px;'>You are the only person with access to your data.</p>
        <p style='font-size: 18px;'>The projects you create are also available only to you and only in the particular browser in which they were created.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

st.title("🎬 Sublyze AI – Auto Subtitle Generator")
st.markdown("Auto Captions for Videos")
st.markdown("""
Create engaging and beautiful subtitles for your video. Right in the browser, for free and 
<a href='?main_nav=Privacy' style='color:#4A90E2; font-weight:bold;'>100% private</a>.
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("📤 Upload your video (MP4/MOV)", type=None)

if uploaded_file and not st.session_state.steps["upload"]:
    file_ext = os.path.splitext(uploaded_file.name)[-1][1:].lower()
    file_size_mb = uploaded_file.size / (1024 * 1024)

    if file_ext not in SUPPORTED_FORMATS:
        st.error("❌ Unsupported file format. Please upload a .mp4 or .mov file.")
        st.stop()

    if file_size_mb > MAX_FILE_SIZE_MB:
        st.error("❌ File too large. Maximum allowed size is 200MB.")
        st.stop()

    video_path = save_uploaded_file(uploaded_file)
    st.session_state.video_path = video_path
    st.session_state.steps["upload"] = True

    with st.spinner("🔊 Extracting audio..."):
        audio_path = extract_audio(video_path)
        st.session_state.steps["extract"] = True

    with st.spinner("🧠 Transcribing the audio..."):
        transcript, chunks = transcribe_audio(audio_path)

        if not transcript.strip():
            st.error("❌ No voice detected in video. Please upload a file with spoken content.")
            st.button("🔁 Try Another Video")
            st.stop()

        st.session_state.transcript = transcript
        st.session_state.chunks = chunks
        st.session_state.steps["transcribe"] = True

    with st.spinner("🧾 Generating subtitles (.srt)..."):
        srt_text = generate_srt(st.session_state.chunks)
        srt_path = save_srt(srt_text)
        st.session_state.steps["subtitle"] = True
        st.download_button("📥 Download Subtitles (.srt)", srt_text, file_name="sublyze_output.srt", key="srt_download_button")

    with st.spinner("🔥 Burning subtitles into video..."):
        try:
            burned_video_path = burn_subtitles_to_video(
                video_path,
                st.session_state.chunks,
                fontsize=st.session_state.font_size,
                color=st.session_state.text_color,
                bg_color=st.session_state.bg_color,
                bg_opacity=st.session_state.bg_opacity
            )
            st.session_state.burned_video_path = burned_video_path
            st.session_state.steps["burn"] = True
        except Exception as e:
            st.error(f"⚠️ Something went wrong while generating the video: {e}. You can still download the subtitles as a .srt file.")
            st.download_button("📥 Download Subtitles (.srt)", srt_text, file_name="sublyze_output.srt", key="srt_download_fallback")
            st.button("🔁 Try Rendering Again")

if any(st.session_state.steps.values()):
    st.markdown("### 🚀 Progress Tracker")
    cols = st.columns(5)
    labels = ["Upload", "Extract", "Transcribe", "Subtitles", "Burn"]
    keys = ["upload", "extract", "transcribe", "subtitle", "burn"]
    for col, label, key in zip(cols, labels, keys):
        status = "✅" if st.session_state.steps[key] else "⬜"
        col.markdown(f"{status} **{label}**")

if st.session_state.video_path and st.session_state.chunks:
    if st.session_state.burned_video_path:
        st.video(st.session_state.burned_video_path, format="video/mp4")
        with open(st.session_state.burned_video_path, "rb") as f:
            st.download_button("📥 Download Video with Subtitles", f, file_name="sublyze_output.mp4", key="video_download_button")

    st.sidebar.title("⚙️ Customization Panel")
    st.session_state.active_tab = st.sidebar.radio("Choose Tab", ["Edit Subtitles", "Style Settings", "Translate Subtitles"], index=["Edit Subtitles", "Style Settings", "Translate Subtitles"].index(st.session_state.active_tab))

    if st.session_state.active_tab == "Edit Subtitles":
        updated_chunks = []
        edited = False

        for i, chunk in enumerate(st.session_state.chunks):
            original_text = chunk["text"]
            start_ts = chunk['timestamp'][0]
            end_ts = chunk['timestamp'][1]
            edited_text = st.sidebar.text_area(f"{i+1}. [{start_ts:.2f} - {end_ts:.2f} sec]", original_text, key=f"edit_{i}")

            if edited_text.strip() != original_text.strip():
                edited = True

            updated_chunks.append({
                "timestamp": chunk["timestamp"],
                "text": edited_text.strip()
            })

        if edited:
            st.sidebar.markdown("---")
            if st.sidebar.button("🔥 Reburn with Edits"):
                with st.spinner("🔁 Re-burning video with updated subtitles..."):
                    try:
                        new_burned_path = burn_subtitles_to_video(
                            st.session_state.video_path,
                            updated_chunks,
                            fontsize=st.session_state.font_size,
                            color=st.session_state.text_color,
                            bg_color=st.session_state.bg_color,
                            bg_opacity=st.session_state.bg_opacity
                        )
                        st.session_state.burned_video_path = new_burned_path
                        st.session_state.chunks = updated_chunks
                        st.success("✅ Updated video generated!")
                        st.rerun()
                    except Exception as e:
                        st.error("⚠️ Failed to generate updated video. Please try again.")
                        st.stop()

    elif st.session_state.active_tab == "Style Settings":
        st.sidebar.markdown("## 🎨 Subtitle Style")

        font_size = st.sidebar.slider("Font Size", min_value=16, max_value=48, value=st.session_state.font_size, key="font_slider")
        text_color = st.sidebar.color_picker("Text Color", st.session_state.text_color or "#FFFFFF", key="text_color_picker")
        bg_color_input = st.sidebar.color_picker("Background Color (Optional)", st.session_state.bg_color or "#000000", key="bg_color_picker")
        bg_color = bg_color_input if bg_color_input != "#000000" else None
        bg_opacity = st.sidebar.slider("Background Opacity", min_value=0.0, max_value=1.0, step=0.01, value=st.session_state.bg_opacity, key="bg_opacity_slider")

        style_changed = (
            font_size != st.session_state.font_size or
            text_color != st.session_state.text_color or
            bg_color != st.session_state.bg_color or
            bg_opacity != st.session_state.bg_opacity
        )

        if style_changed:
            if st.sidebar.button("🔥 Reburn with Style Changes"):
                with st.spinner("🎬 Applying new styles and burning video..."):
                    try:
                        st.session_state.font_size = font_size
                        st.session_state.text_color = text_color
                        st.session_state.bg_color = bg_color
                        st.session_state.bg_opacity = bg_opacity

                        new_burned_path = burn_subtitles_to_video(
                            st.session_state.video_path,
                            st.session_state.chunks,
                            fontsize=st.session_state.font_size,
                            color=st.session_state.text_color,
                            bg_color=st.session_state.bg_color,
                            bg_opacity=st.session_state.bg_opacity
                        )
                        st.session_state.burned_video_path = new_burned_path
                        st.success("✅ Style updated and video re-burned!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Failed to apply styles. Reason: {e}")

        st.sidebar.markdown("---")
        st.sidebar.markdown("🔍 **Live Subtitle Style Preview**")
        preview_text = "This is a sample subtitle."
        rgba = tuple(int(bg_color_input.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (bg_opacity,)
        rgba_str = f"rgba({rgba[0]}, {rgba[1]}, {rgba[2]}, {rgba[3]})" if bg_color else "transparent"
        preview_style = f"<div style='padding: 10px; border-radius: 12px; background-color: {rgba_str}; color: {text_color}; font-size: {font_size}px; text-align: center;'> {preview_text} </div>"
        st.sidebar.markdown(preview_style, unsafe_allow_html=True)

    elif st.session_state.active_tab == "Translate Subtitles":
        st.sidebar.markdown("## 🌍 Translate Subtitles")

        translation_languages = {
            "English": "eng_Latn",   
            "French": "fra_Latn",
            "Spanish": "spa_Latn",
            "German": "deu_Latn",
            "Italian": "ita_Latn",
            "Portuguese": "por_Latn",
            "Chinese": "zho_Hans"
        }

        selected_lang = st.sidebar.selectbox("Select target language:", list(translation_languages.keys()))

        if st.sidebar.button("🌐 Translate and Reburn"):
            with st.spinner("Translating subtitles and generating video..."):
                try:
                    model_name = "facebook/nllb-200-distilled-600M"
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

                    tokenizer.src_lang = "eng_Latn"
                    target_lang_code = translation_languages[selected_lang]

                    # 🔥 This is the correct way!
                    forced_bos_token_id = tokenizer.convert_tokens_to_ids(target_lang_code)

                    translated_chunks = []

                    for chunk in st.session_state.chunks:
                        input_text = chunk["text"]
                        inputs = tokenizer(input_text, return_tensors="pt", padding=True)

                        outputs = model.generate(
                            **inputs,
                            forced_bos_token_id=forced_bos_token_id  # 👈 Force correct target language here
                        )

                        translated_text = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]

                        translated_chunks.append({
                            "timestamp": chunk["timestamp"],
                            "text": translated_text
                        })

                    st.session_state.chunks = translated_chunks
                    new_burned_path = burn_subtitles_to_video(
                        st.session_state.video_path,
                        translated_chunks,
                        fontsize=st.session_state.font_size,
                        color=st.session_state.text_color,
                        bg_color=st.session_state.bg_color,
                        bg_opacity=st.session_state.bg_opacity
                    )
                    st.session_state.burned_video_path = new_burned_path
                    st.success("✅ Subtitles translated and video updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"⚠️ Translation failed: {e}")



