import streamlit as st
import os
import time
import uuid
from utils.audio_utils import save_uploaded_file, extract_audio
from utils.transcription import transcribe_audio
from utils.subtitle_utils import generate_srt, save_srt, burn_subtitles_to_video

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sublyze AI – Auto Subtitle Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0d0d1a 0%, #1a1a2e 55%, #16213e 100%);
    min-height: 100vh;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] > div:first-child {
    background: rgba(10, 10, 25, 0.98) !important;
    border-right: 1px solid rgba(102, 126, 234, 0.12);
}

/* ── Typography ── */
h1, h2, h3, h4 { color: #f0f0ff !important; }

/* ── Hero ── */
.hero-title {
    font-size: clamp(2.4rem, 5vw, 3.8rem);
    font-weight: 900;
    background: linear-gradient(90deg, #667eea 0%, #a855f7 50%, #ec4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.15;
    margin: 0 0 10px 0;
    letter-spacing: -0.02em;
}
.hero-sub {
    color: #7070a0 !important;
    font-size: 1.1rem;
    margin-bottom: 22px;
}

/* ── Badge pills ── */
.badge-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 32px; }
.badge {
    padding: 5px 14px; border-radius: 100px;
    font-size: 0.75rem; font-weight: 700; letter-spacing: 0.04em;
}
.badge-purple { background: rgba(168,85,247,0.14); border: 1px solid rgba(168,85,247,0.35); color: #c084fc; }
.badge-blue   { background: rgba(102,126,234,0.14); border: 1px solid rgba(102,126,234,0.35); color: #93c5fd; }
.badge-green  { background: rgba(52,211,153,0.14);  border: 1px solid rgba(52,211,153,0.35);  color: #6ee7b7; }
.badge-pink   { background: rgba(236,72,153,0.12);  border: 1px solid rgba(236,72,153,0.30);  color: #f9a8d4; }

/* ── Landing feature grid ── */
.feat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px; margin: 0 0 32px 0;
}
.feat-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 18px; padding: 24px 20px;
    transition: border-color 0.2s, transform 0.2s;
}
.feat-card:hover { border-color: rgba(102,126,234,0.3); transform: translateY(-2px); }
.feat-icon  { font-size: 2rem; margin-bottom: 12px; }
.feat-name  { font-size: 0.95rem; font-weight: 700; color: #d0d0f0 !important; margin-bottom: 6px; }
.feat-desc  { font-size: 0.8rem; color: #505075 !important; line-height: 1.55; }

/* ── Progress pipeline ── */
.pipeline {
    display: flex; align-items: flex-start; gap: 0;
    padding: 22px 24px;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 18px; margin: 20px 0;
}
.pipe-step  { display: flex; flex-direction: column; align-items: center; flex: 1; }
.pipe-icon  {
    width: 40px; height: 40px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; font-weight: 800; position: relative; z-index: 1;
}
.pipe-done .pipe-icon {
    background: linear-gradient(135deg, #34d399, #10b981);
    box-shadow: 0 0 18px rgba(52,211,153,0.45); color: #fff;
}
.pipe-active .pipe-icon {
    background: linear-gradient(135deg, #667eea, #a855f7);
    box-shadow: 0 0 22px rgba(102,126,234,0.6); color: #fff;
    animation: glow 1.6s ease-in-out infinite;
}
.pipe-pending .pipe-icon {
    background: rgba(255,255,255,0.05);
    border: 2px solid rgba(255,255,255,0.09); color: #333;
}
.pipe-lbl {
    font-size: 0.62rem; text-transform: uppercase;
    letter-spacing: 0.07em; font-weight: 700; margin-top: 8px;
}
.pipe-done .pipe-lbl    { color: #34d399 !important; }
.pipe-active .pipe-lbl  { color: #93c5fd !important; }
.pipe-pending .pipe-lbl { color: #303050 !important; }
.pipe-line      { flex: 1; height: 2px; background: rgba(255,255,255,0.05); margin-bottom: 24px; }
.pipe-line-done { background: linear-gradient(90deg, #10b981, #34d399); }

@keyframes glow {
    0%,100% { box-shadow: 0 0 22px rgba(102,126,234,0.6); }
    50%      { box-shadow: 0 0 36px rgba(102,126,234,0.9); }
}

/* ── Stats row ── */
.stats-row { display: flex; gap: 14px; flex-wrap: wrap; margin: 20px 0 28px 0; }
.stat-card {
    flex: 1; min-width: 110px;
    background: rgba(102,126,234,0.08);
    border: 1px solid rgba(102,126,234,0.2);
    border-radius: 14px; padding: 16px 18px; text-align: center;
}
.stat-val {
    font-size: 1.8rem; font-weight: 800;
    background: linear-gradient(90deg, #667eea, #a855f7);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.stat-lbl {
    font-size: 0.68rem; color: #505080 !important;
    text-transform: uppercase; letter-spacing: 0.07em; margin-top: 4px;
}

/* ── Video player ── */
video {
    border-radius: 14px !important;
    box-shadow: 0 24px 64px rgba(0,0,0,0.6) !important;
    width: 100% !important; max-height: 62vh !important;
    object-fit: contain !important; background: #000;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #667eea, #a855f7) !important;
    color: #fff !important; border: none !important;
    border-radius: 10px !important; font-weight: 700 !important;
    padding: 0.5rem 1.4rem !important; letter-spacing: 0.02em !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 28px rgba(102,126,234,0.4) !important;
}
.stDownloadButton > button {
    background: rgba(52,211,153,0.1) !important; color: #34d399 !important;
    border: 1px solid rgba(52,211,153,0.3) !important;
    border-radius: 10px !important; font-weight: 700 !important;
}
.stDownloadButton > button:hover {
    background: rgba(52,211,153,0.2) !important;
    box-shadow: 0 6px 20px rgba(52,211,153,0.2) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploadDropzone"] {
    background: rgba(102,126,234,0.05) !important;
    border: 2px dashed rgba(102,126,234,0.3) !important;
    border-radius: 16px !important; transition: all 0.2s !important;
}
[data-testid="stFileUploadDropzone"]:hover {
    background: rgba(102,126,234,0.1) !important;
    border-color: rgba(102,126,234,0.55) !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #667eea !important; }

/* ── Sidebar text ── */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #d0d0f0 !important; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown { color: #8080a0 !important; }

/* ── Subtitle editor ── */
.stTextArea textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important; color: #d0d0f0 !important;
    font-size: 0.84rem !important;
}
.stTextArea textarea:focus {
    border-color: rgba(102,126,234,0.5) !important;
    box-shadow: 0 0 0 2px rgba(102,126,234,0.15) !important;
}

/* ── Footer ── */
.footer {
    text-align: center; padding: 28px 0 12px 0;
    border-top: 1px solid rgba(255,255,255,0.05);
    margin-top: 52px; color: #303050 !important; font-size: 0.8rem;
}
.footer a { color: #667eea !important; text-decoration: none; }
.footer a:hover { color: #a855f7 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(102,126,234,0.3); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
def _init_session():
    """Initialise missing session state keys with fresh default values.

    Using a function (not a module-level dict) prevents the shared-reference
    bug where mutating st.session_state.steps also mutates the defaults dict.
    """
    defaults = {
        'session_id':        uuid.uuid4().hex[:12],
        'video_path':        None,
        'audio_path':        None,
        'srt_path':          None,
        'srt_content':       None,
        'chunks':            None,
        'transcript':        None,
        'burned_video_path': None,
        'font_size':         18,
        'text_color':        '#FFFFFF',
        'bg_color':          '#000000',
        'bg_opacity':        0.6,
        'active_tab':        'Edit Subtitles',
        'steps':             {k: False for k in ['upload','extract','transcribe','subtitle','burn']},
        'stats':             {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_session()

SUPPORTED_FORMATS = ["mp4", "mov"]
MAX_FILE_MB = 200

# ── Helper functions ──────────────────────────────────────────────────────────
def fmt_duration(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def _pipeline_html() -> str:
    """Build the animated 5-step progress pipeline as an HTML string."""
    steps = [
        ('upload',     '📤', 'Upload'),
        ('extract',    '🔊', 'Extract'),
        ('transcribe', '🧠', 'Transcribe'),
        ('subtitle',   '📝', 'Subtitles'),
        ('burn',       '🔥', 'Burn'),
    ]
    done_count = sum(1 for k, _, _ in steps if st.session_state.steps[k])
    # Active = first step not yet marked done (pulsing purple)
    active_idx = done_count if done_count < len(steps) else -1

    html = '<div class="pipeline">'
    for i, (key, icon, label) in enumerate(steps):
        if st.session_state.steps[key]:
            cls, content = 'pipe-done', '✓'
        elif i == active_idx:
            cls, content = 'pipe-active', icon
        else:
            cls, content = 'pipe-pending', icon

        html += (
            f'<div class="pipe-step {cls}">'
            f'  <div class="pipe-icon">{content}</div>'
            f'  <div class="pipe-lbl">{label}</div>'
            f'</div>'
        )
        if i < len(steps) - 1:
            line_cls = 'pipe-line-done' if st.session_state.steps[key] else ''
            html += f'<div class="pipe-line {line_cls}"></div>'

    html += '</div>'
    return html


def _stats_html() -> str:
    s = st.session_state.stats
    if not s:
        return ''
    items = [
        (s.get('segments', '—'), 'Segments'),
        (s.get('words',    '—'), 'Words'),
        (s.get('duration', '—'), 'Duration'),
        (s.get('proc_time','—'), 'Processed in'),
    ]
    html = '<div class="stats-row">'
    for val, lbl in items:
        html += (
            f'<div class="stat-card">'
            f'  <div class="stat-val">{val}</div>'
            f'  <div class="stat-lbl">{lbl}</div>'
            f'</div>'
        )
    html += '</div>'
    return html


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎬 Sublyze AI")
    page = st.radio("Navigate", ["✂️ Editor", "🔒 Privacy"], label_visibility="collapsed")
    st.markdown("---")

    if page == "✂️ Editor" and st.session_state.chunks:
        st.markdown("### ⚙️ Customization")
        tab_choice = st.radio(
            "Panel",
            ["Edit Subtitles", "Style Settings"],
            index=["Edit Subtitles", "Style Settings"].index(st.session_state.active_tab),
            label_visibility="collapsed",
        )
        st.session_state.active_tab = tab_choice
        st.markdown("---")

        # ── Edit Subtitles tab ─────────────────────────────────────────────
        if tab_choice == "Edit Subtitles":
            st.markdown("**✏️ Edit Subtitle Segments**")
            updated_chunks, edited = [], False
            for i, chunk in enumerate(st.session_state.chunks):
                s, e = chunk['timestamp']
                new_text = st.text_area(
                    f"{i+1}. [{fmt_duration(s)} – {fmt_duration(e)}]",
                    chunk["text"],
                    key=f"edit_{i}",
                    height=64,
                )
                if new_text.strip() != chunk["text"].strip():
                    edited = True
                updated_chunks.append({"timestamp": chunk["timestamp"], "text": new_text.strip()})

            if edited:
                st.markdown("---")
                if st.button("🔥 Re-burn with Edits", use_container_width=True):
                    with st.spinner("Re-burning with edited subtitles…"):
                        try:
                            path = burn_subtitles_to_video(
                                st.session_state.video_path,
                                updated_chunks,
                                fontsize   = st.session_state.font_size,
                                color      = st.session_state.text_color,
                                bg_color   = st.session_state.bg_color,
                                bg_opacity = st.session_state.bg_opacity,
                                session_id = st.session_state.session_id,
                            )
                            st.session_state.burned_video_path = path
                            st.session_state.chunks = updated_chunks
                            st.session_state.srt_content = generate_srt(updated_chunks)
                            st.success("✅ Video updated!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Re-burn failed: {err}")

        # ── Style Settings tab ─────────────────────────────────────────────
        elif tab_choice == "Style Settings":
            st.markdown("**🎨 Subtitle Style**")
            font_size  = st.slider("Font Size", 12, 52, st.session_state.font_size)
            text_color = st.color_picker("Text Color",       st.session_state.text_color)
            bg_color   = st.color_picker("Background Color", st.session_state.bg_color)
            bg_opacity = st.slider("Background Opacity", 0.0, 1.0,
                                   st.session_state.bg_opacity, step=0.05)

            # Live style preview
            preview_rgb  = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            preview_rgba = f"rgba({preview_rgb[0]},{preview_rgb[1]},{preview_rgb[2]},{bg_opacity})"
            st.markdown("**Preview**")
            st.markdown(
                f"<div style='padding:10px 16px;border-radius:10px;"
                f"background:{preview_rgba};color:{text_color};"
                f"font-size:{font_size}px;text-align:center;font-weight:700;'>"
                f"This is a sample subtitle.</div>",
                unsafe_allow_html=True,
            )

            style_changed = (
                font_size  != st.session_state.font_size  or
                text_color != st.session_state.text_color or
                bg_color   != st.session_state.bg_color   or
                bg_opacity != st.session_state.bg_opacity
            )
            if style_changed:
                st.markdown("---")
                if st.button("🎬 Apply & Re-burn", use_container_width=True):
                    with st.spinner("Applying new styles…"):
                        try:
                            st.session_state.font_size  = font_size
                            st.session_state.text_color = text_color
                            st.session_state.bg_color   = bg_color
                            st.session_state.bg_opacity = bg_opacity
                            path = burn_subtitles_to_video(
                                st.session_state.video_path,
                                st.session_state.chunks,
                                fontsize   = font_size,
                                color      = text_color,
                                bg_color   = bg_color,
                                bg_opacity = bg_opacity,
                                session_id = st.session_state.session_id,
                            )
                            st.session_state.burned_video_path = path
                            st.success("✅ Styles applied!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Style burn failed: {err}")


# ── Privacy page ──────────────────────────────────────────────────────────────
if page == "🔒 Privacy":
    st.markdown("## 🔐 Privacy & Data Handling")
    st.markdown("""
    **How Sublyze AI processes your video:**

    - Your video is uploaded temporarily to our processing server
    - Audio is extracted and transcribed on-server using OpenAI Whisper (self-hosted, open-source)
    - All temporary files (WAV, SRT, burned MP4) are tied to your session and deleted when you leave
    - We do **not** store, share, or train on your videos

    **Tech stack:**
    | Component | Tool |
    |---|---|
    | 🤖 Transcription | OpenAI Whisper (self-hosted via HuggingFace) |
    | 🎬 Video burning | FFmpeg (libass subtitle filter) |
    | 📝 Subtitle format | SRT (open standard) |
    | 🚀 Hosting | Streamlit Cloud |

    > **Transparency note:** Processing runs on our server — not in your browser.
    > Your data is handled securely and is never persisted beyond your session.
    """)
    st.stop()


# ── Main Editor page ──────────────────────────────────────────────────────────

# Hero
st.markdown("""
<div style="padding: 24px 0 8px 0;">
  <div class="hero-title">Sublyze AI</div>
  <div class="hero-sub">Auto-generate burned-in subtitles for any video — free, in one click.</div>
</div>
<div class="badge-row">
  <span class="badge badge-purple">🤖 Whisper AI</span>
  <span class="badge badge-blue">⚡ FFmpeg libass</span>
  <span class="badge badge-green">🎯 One-click</span>
  <span class="badge badge-pink">✏️ Editable Subtitles</span>
</div>
""", unsafe_allow_html=True)

# Feature grid (landing — shown only before first upload)
if not st.session_state.steps['upload']:
    st.markdown("""
    <div class="feat-grid">
      <div class="feat-card">
        <div class="feat-icon">🧠</div>
        <div class="feat-name">AI Transcription</div>
        <div class="feat-desc">OpenAI Whisper detects speech with high accuracy across 90+ languages — no API key required.</div>
      </div>
      <div class="feat-card">
        <div class="feat-icon">🔥</div>
        <div class="feat-name">Burned-in Subtitles</div>
        <div class="feat-desc">Subtitles are hard-coded into your video via FFmpeg. Works on every player, every platform.</div>
      </div>
      <div class="feat-card">
        <div class="feat-icon">✏️</div>
        <div class="feat-name">Edit & Restyle</div>
        <div class="feat-desc">Fix transcription errors, change font size, colors and background opacity with a live preview.</div>
      </div>
      <div class="feat-card">
        <div class="feat-icon">📥</div>
        <div class="feat-name">Export Anywhere</div>
        <div class="feat-desc">Download the subtitled MP4 or the raw .SRT file to use in any video editor or media player.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# File uploader — keyed so Start Over can force a full widget reset
uploaded_file = st.file_uploader(
    "📤 Drop your video here or click to browse",
    type=SUPPORTED_FORMATS,
    help=f"Supported: MP4, MOV · Max {MAX_FILE_MB} MB",
    key=f"uploader_{st.session_state.session_id}",
)

# Pipeline placeholder — sits at a fixed position; updated in-place during processing
pipeline_ph = st.empty()
if any(st.session_state.steps.values()):
    pipeline_ph.markdown(_pipeline_html(), unsafe_allow_html=True)

# ── Processing pipeline (runs only once per upload) ───────────────────────────
if uploaded_file and not st.session_state.steps["upload"]:
    file_ext = os.path.splitext(uploaded_file.name)[-1][1:].lower()
    file_mb  = uploaded_file.size / (1024 * 1024)

    if file_ext not in SUPPORTED_FORMATS:
        st.error("❌ Unsupported format. Please upload an MP4 or MOV file.")
        st.stop()
    if file_mb > MAX_FILE_MB:
        st.error(f"❌ File too large ({file_mb:.1f} MB). Maximum is {MAX_FILE_MB} MB.")
        st.stop()

    t_start = time.time()

    # Show pipeline with Upload as the active step
    pipeline_ph.markdown(_pipeline_html(), unsafe_allow_html=True)

    # ── Step 1: Save ──────────────────────────────────────────────────────
    video_path = save_uploaded_file(uploaded_file)
    st.session_state.video_path = video_path
    st.session_state.steps["upload"] = True
    pipeline_ph.markdown(_pipeline_html(), unsafe_allow_html=True)

    # ── Step 2: Extract audio ─────────────────────────────────────────────
    with st.spinner("🔊 Extracting audio…"):
        audio_path = extract_audio(video_path)
        st.session_state.audio_path = audio_path
        st.session_state.steps["extract"] = True
    pipeline_ph.markdown(_pipeline_html(), unsafe_allow_html=True)

    # ── Step 3: Transcribe ────────────────────────────────────────────────
    with st.spinner("🧠 Transcribing with Whisper AI… (30–60 s on first run)"):
        transcript, chunks = transcribe_audio(audio_path)

    if not transcript.strip():
        st.error("❌ No speech detected. Please upload a video with spoken audio.")
        if st.button("🔁 Try a Different Video"):
            st.session_state.clear()
            st.rerun()
        st.stop()

    st.session_state.transcript = transcript
    st.session_state.chunks     = chunks
    st.session_state.steps["transcribe"] = True

    # Compute stats
    duration_s = chunks[-1]['timestamp'][1] if chunks else 0
    st.session_state.stats = {
        'segments':  len(chunks),
        'words':     len(transcript.split()),
        'duration':  fmt_duration(duration_s),
        'proc_time': '',             # filled after burn
    }
    pipeline_ph.markdown(_pipeline_html(), unsafe_allow_html=True)

    # ── Step 4: Generate SRT ──────────────────────────────────────────────
    with st.spinner("📝 Generating subtitle file…"):
        os.makedirs("data", exist_ok=True)
        srt_text = generate_srt(chunks)
        srt_path = save_srt(srt_text, f"data/subtitles_{st.session_state.session_id}.srt")
        st.session_state.srt_path    = srt_path
        st.session_state.srt_content = srt_text
        st.session_state.steps["subtitle"] = True
    pipeline_ph.markdown(_pipeline_html(), unsafe_allow_html=True)

    # ── Step 5: Burn subtitles ────────────────────────────────────────────
    with st.spinner("🔥 Burning subtitles into video…"):
        try:
            burned_path = burn_subtitles_to_video(
                video_path, chunks,
                fontsize   = st.session_state.font_size,
                color      = st.session_state.text_color,
                bg_color   = st.session_state.bg_color,
                bg_opacity = st.session_state.bg_opacity,
                session_id = st.session_state.session_id,
            )
            st.session_state.burned_video_path = burned_path
            st.session_state.steps["burn"]     = True
        except Exception as err:
            st.error(
                f"⚠️ Subtitle burning failed.\n\n**Error:** `{err}`\n\n"
                f"You can still download the `.SRT` file below and use it in any video editor."
            )
    pipeline_ph.markdown(_pipeline_html(), unsafe_allow_html=True)

    elapsed = time.time() - t_start
    st.session_state.stats['proc_time'] = f"{elapsed:.0f} s"

    if st.session_state.steps["burn"]:
        st.success(f"✅ Done in **{elapsed:.1f} s** — your subtitled video is ready!")
    else:
        st.warning("⚠️ Video burning failed, but your subtitle file (.SRT) is ready to download.")


# ── Results section ───────────────────────────────────────────────────────────
if st.session_state.steps["burn"] and st.session_state.burned_video_path:
    # Stats bar
    stats_html = _stats_html()
    if stats_html:
        st.markdown(stats_html, unsafe_allow_html=True)

    st.markdown("### 🎬 Your Subtitled Video")
    st.video(st.session_state.burned_video_path, format="video/mp4")

    col_a, col_b, col_c = st.columns([1, 1, 2])
    with col_a:
        with open(st.session_state.burned_video_path, "rb") as f:
            st.download_button(
                "📥 Download Video",
                f,
                file_name="sublyze_output.mp4",
                mime="video/mp4",
                key="dl_video",
                use_container_width=True,
            )
    with col_b:
        if st.session_state.srt_content:
            st.download_button(
                "📄 Download .SRT",
                st.session_state.srt_content,
                file_name="sublyze_subtitles.srt",
                mime="text/plain",
                key="dl_srt",
                use_container_width=True,
            )
    with col_c:
        if st.button("🔄 Start Over — Upload New Video", use_container_width=True):
            st.session_state.clear()   # wipes all state + resets file uploader widget
            st.rerun()

elif st.session_state.steps["subtitle"] and not st.session_state.steps["burn"]:
    # Burn failed fallback — still offer SRT
    if st.session_state.srt_content:
        st.download_button(
            "📄 Download Subtitles (.SRT)",
            st.session_state.srt_content,
            file_name="sublyze_subtitles.srt",
            key="dl_srt_fallback",
        )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
  Built with ❤️ using
  <a href="https://openai.com/research/whisper" target="_blank">OpenAI Whisper</a>,
  <a href="https://ffmpeg.org" target="_blank">FFmpeg</a> &amp;
  <a href="https://streamlit.io" target="_blank">Streamlit</a> ·
  <a href="https://github.com/Sahil081997/sublyze-ai" target="_blank">⭐ View on GitHub</a>
</div>
""", unsafe_allow_html=True)

