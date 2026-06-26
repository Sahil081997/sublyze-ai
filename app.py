import streamlit as st
import os
import time
import uuid
from utils.audio_utils import save_uploaded_file, extract_audio
from utils.transcription import transcribe_audio
from utils.subtitle_utils import (
    generate_srt, save_srt, burn_subtitles_to_video,
    merge_short_segments, PRESET_STYLES,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sublyze AI – Auto Subtitle Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg,#0d0d1a 0%,#1a1a2e 55%,#16213e 100%);
    min-height:100vh;
}
[data-testid="stHeader"]          { background:transparent !important; }
[data-testid="stSidebar"]>div:first-child {
    background:rgba(8,8,20,0.99) !important;
    border-right:1px solid rgba(102,126,234,0.10);
    padding:0 !important;
}
h1,h2,h3,h4 { color:#f0f0ff !important; }

/* ── Hero ── */
.hero-title {
    font-size:clamp(2.2rem,5vw,3.6rem); font-weight:900;
    background:linear-gradient(90deg,#667eea 0%,#a855f7 50%,#ec4899 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text; line-height:1.15; margin:0 0 10px 0;
}
.hero-sub { color:#7070a0 !important; font-size:1.05rem; margin-bottom:20px; }

/* ── Badges ── */
.badge-row { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:28px; }
.badge { padding:5px 14px; border-radius:100px; font-size:.75rem; font-weight:700; letter-spacing:.04em; }
.badge-purple { background:rgba(168,85,247,.14); border:1px solid rgba(168,85,247,.35); color:#c084fc; }
.badge-blue   { background:rgba(102,126,234,.14); border:1px solid rgba(102,126,234,.35); color:#93c5fd; }
.badge-green  { background:rgba(52,211,153,.14);  border:1px solid rgba(52,211,153,.35);  color:#6ee7b7; }
.badge-pink   { background:rgba(236,72,153,.12);  border:1px solid rgba(236,72,153,.30);  color:#f9a8d4; }

/* ── Feature grid ── */
.feat-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:14px; margin:0 0 28px; }
.feat-card { background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07); border-radius:16px; padding:20px; transition:.2s; }
.feat-card:hover { border-color:rgba(102,126,234,.3); transform:translateY(-2px); }
.feat-icon { font-size:1.8rem; margin-bottom:10px; }
.feat-name { font-size:.9rem; font-weight:700; color:#d0d0f0 !important; margin-bottom:5px; }
.feat-desc { font-size:.78rem; color:#4a4a70 !important; line-height:1.5; }

/* ── Progress pipeline ── */
.pipeline { display:flex; align-items:flex-start; padding:18px 22px; background:rgba(255,255,255,.025); border:1px solid rgba(255,255,255,.06); border-radius:16px; margin:18px 0; }
.pipe-step { display:flex; flex-direction:column; align-items:center; flex:1; }
.pipe-icon { width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:.95rem; font-weight:800; }
.pipe-done   .pipe-icon { background:linear-gradient(135deg,#34d399,#10b981); box-shadow:0 0 16px rgba(52,211,153,.45); color:#fff; }
.pipe-active .pipe-icon { background:linear-gradient(135deg,#667eea,#a855f7); box-shadow:0 0 20px rgba(102,126,234,.6); color:#fff; animation:glow 1.6s ease-in-out infinite; }
.pipe-pending .pipe-icon { background:rgba(255,255,255,.05); border:2px solid rgba(255,255,255,.09); color:#333; }
.pipe-lbl { font-size:.6rem; text-transform:uppercase; letter-spacing:.07em; font-weight:700; margin-top:7px; }
.pipe-done   .pipe-lbl { color:#34d399 !important; }
.pipe-active .pipe-lbl { color:#93c5fd !important; }
.pipe-pending .pipe-lbl{ color:#303050 !important; }
.pipe-line      { flex:1; height:2px; background:rgba(255,255,255,.05); margin-bottom:22px; }
.pipe-line-done { background:linear-gradient(90deg,#10b981,#34d399); }
@keyframes glow { 0%,100%{box-shadow:0 0 20px rgba(102,126,234,.6);}50%{box-shadow:0 0 34px rgba(102,126,234,.9);} }

/* ── Stats ── */
.stats-row { display:flex; gap:12px; flex-wrap:wrap; margin:16px 0 24px; }
.stat-card { flex:1; min-width:100px; background:rgba(102,126,234,.08); border:1px solid rgba(102,126,234,.2); border-radius:12px; padding:14px 16px; text-align:center; }
.stat-val  { font-size:1.6rem; font-weight:800; background:linear-gradient(90deg,#667eea,#a855f7); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.stat-lbl  { font-size:.65rem; color:#505080 !important; text-transform:uppercase; letter-spacing:.07em; margin-top:3px; }

/* ── Video ── */
video { border-radius:14px !important; box-shadow:0 20px 56px rgba(0,0,0,.6) !important; width:100% !important; max-height:58vh !important; object-fit:contain !important; background:#000; }

/* ── Preset tiles ── */
.preset-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-bottom:16px; }
.preset-tile {
    background:rgba(255,255,255,.03); border:2px solid rgba(255,255,255,.08);
    border-radius:12px; padding:10px 8px; text-align:center; cursor:pointer; transition:.15s;
}
.preset-tile:hover { border-color:rgba(102,126,234,.4); transform:translateY(-1px); }
.preset-tile.active { border-color:#667eea; background:rgba(102,126,234,.12); }
.preset-emoji { font-size:1.4rem; }
.preset-name  { font-size:.72rem; font-weight:700; color:#c0c0e0 !important; margin-top:4px; }
.preset-desc  { font-size:.6rem; color:#505075 !important; margin-top:3px; line-height:1.35; }

/* ── Style section headers ── */
.style-section {
    font-size:.7rem; font-weight:700; text-transform:uppercase;
    letter-spacing:.08em; color:#667eea !important;
    border-bottom:1px solid rgba(102,126,234,.2);
    padding-bottom:6px; margin:16px 0 10px;
}

/* ── Segment cards ── */
.seg-header { display:flex; align-items:center; gap:8px; margin-bottom:4px; }
.seg-num  { font-size:.65rem; font-weight:700; color:#667eea !important; min-width:22px; }
.seg-time { font-size:.65rem; color:#404060 !important; font-family:monospace; flex:1; }
.seg-dur  { font-size:.6rem; font-weight:700; padding:2px 7px; border-radius:4px; }
.seg-dur-ok    { background:rgba(52,211,153,.15); color:#34d399 !important; }
.seg-dur-short { background:rgba(251,191,36,.15); color:#fbbf24 !important; }
.seg-dur-vshort{ background:rgba(239,68,68,.15);  color:#f87171 !important; }
.seg-chars { font-size:.58rem; color:#404060 !important; }

/* ── Buttons ── */
.stButton>button {
    background:linear-gradient(135deg,#667eea,#a855f7) !important; color:#fff !important;
    border:none !important; border-radius:10px !important; font-weight:700 !important;
    transition:transform .15s,box-shadow .15s !important;
}
.stButton>button:hover { transform:translateY(-2px) !important; box-shadow:0 10px 28px rgba(102,126,234,.4) !important; }
.stDownloadButton>button {
    background:rgba(52,211,153,.1) !important; color:#34d399 !important;
    border:1px solid rgba(52,211,153,.3) !important; border-radius:10px !important; font-weight:700 !important;
}
.stDownloadButton>button:hover { background:rgba(52,211,153,.2) !important; }

/* ── File uploader ── */
[data-testid="stFileUploadDropzone"] {
    background:rgba(102,126,234,.05) !important; border:2px dashed rgba(102,126,234,.3) !important;
    border-radius:16px !important;
}
[data-testid="stFileUploadDropzone"]:hover { background:rgba(102,126,234,.1) !important; border-color:rgba(102,126,234,.55) !important; }

/* ── Misc ── */
.stSpinner>div { border-top-color:#667eea !important; }
.stTextArea textarea { background:rgba(255,255,255,.04) !important; border:1px solid rgba(255,255,255,.1) !important; border-radius:8px !important; color:#d0d0f0 !important; font-size:.84rem !important; }
.stTextArea textarea:focus { border-color:rgba(102,126,234,.5) !important; }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 { color:#d0d0f0 !important; }
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label { color:#8080a0 !important; }

/* ── Sidebar brand ── */
.sb-brand {
    padding:28px 20px 20px;
    border-bottom:1px solid rgba(102,126,234,0.10);
    margin-bottom:8px;
}
.sb-logo {
    display:flex; align-items:center; gap:10px; margin-bottom:4px;
}
.sb-logo-icon {
    width:36px; height:36px; border-radius:10px;
    background:linear-gradient(135deg,#667eea,#a855f7);
    display:flex; align-items:center; justify-content:center;
    font-size:1.1rem; flex-shrink:0;
    box-shadow:0 4px 14px rgba(102,126,234,0.4);
}
.sb-logo-name {
    font-size:1.1rem; font-weight:800; letter-spacing:-.01em;
    background:linear-gradient(90deg,#c0c8ff,#d8b4fe);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text;
}
.sb-logo-tag {
    font-size:.62rem; color:#3a3a5a !important;
    text-transform:uppercase; letter-spacing:.08em; padding-left:46px;
}

/* ── Sidebar nav section label ── */
.sb-nav-label {
    font-size:.6rem; font-weight:700; text-transform:uppercase;
    letter-spacing:.1em; color:#2e2e4e !important;
    padding:6px 20px 4px;
}

/* ── Sidebar nav buttons ── */
[data-testid="stSidebar"] .stButton > button {
    background:transparent !important;
    border:none !important;
    border-radius:10px !important;
    color:#6060a0 !important;
    font-weight:600 !important;
    font-size:.88rem !important;
    text-align:left !important;
    padding:7px 14px !important;
    width:100% !important;
    transition:background .15s,color .15s !important;
    box-shadow:none !important;
    transform:none !important;
    margin-bottom:0 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background:rgba(102,126,234,0.08) !important;
    color:#c0c8ff !important;
    transform:none !important;
    box-shadow:none !important;
}
[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stSidebar"] div.stVerticalBlock {
    gap:2px !important;
}

/* Active nav item — injected via wrapper div with data-active */
.nav-item-active > div > button,
.nav-item-active .stButton > button {
    background:rgba(102,126,234,0.14) !important;
    color:#c0c8ff !important;
    border-left:3px solid #667eea !important;
    padding-left:11px !important;
}

/* ── Sidebar divider ── */
.sb-divider {
    border:none; border-top:1px solid rgba(255,255,255,0.05);
    margin:12px 16px;
}

/* ── Sidebar footer ── */
.sb-footer {
    position:absolute; bottom:0; left:0; right:0;
    padding:16px 20px;
    border-top:1px solid rgba(255,255,255,0.04);
}
.sb-footer-badge {
    display:flex; align-items:center; gap:8px;
    background:rgba(52,211,153,0.07); border:1px solid rgba(52,211,153,0.15);
    border-radius:8px; padding:8px 10px;
}
.sb-footer-dot { width:6px;height:6px;border-radius:50%;background:#34d399;flex-shrink:0;animation:pulse-dot 2s ease-in-out infinite; }
.sb-footer-text { font-size:.72rem; color:#34d399 !important; font-weight:600; }
.sb-version { font-size:.6rem; color:#2a2a44 !important; margin-top:8px; text-align:center; }
@keyframes pulse-dot { 0%,100%{opacity:1;}50%{opacity:.4;} }
.footer { text-align:center; padding:24px 0 10px; border-top:1px solid rgba(255,255,255,.05); margin-top:48px; color:#303050 !important; font-size:.78rem; }
.footer a { color:#667eea !important; text-decoration:none; }
::-webkit-scrollbar { width:5px; background:transparent; }
::-webkit-scrollbar-thumb { background:rgba(102,126,234,.3); border-radius:3px; }
</style>""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
def _init_session():
    defaults = {
        "session_id":        uuid.uuid4().hex[:12],
        "video_path":        None, "audio_path":  None,
        "srt_path":          None, "srt_content": None,
        "chunks":            None, "transcript":  None,
        "burned_video_path": None,
        # style
        "active_preset":  "subtle",
        "font_size":      18,
        "color":          "#FFFFFF",
        "bg_color":       "#000000",
        "bg_opacity":     0.6,
        "border_style":   "box",
        "stroke_color":   "#000000",
        "stroke_width":   0,
        "shadow":         0,
        "position":       "bottom",
        "text_case":      "original",
        # pipeline
        "steps": {k: False for k in ["upload","extract","transcribe","subtitle","burn"]},
        "stats": {},
        "page": "✂️ Editor",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_session()

SUPPORTED_FORMATS = ["mp4", "mov"]
MAX_FILE_MB = 200


# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_dur(s: float) -> str:
    m, sec = divmod(int(s), 60)
    return f"{m}:{sec:02d}"


def _pipeline_html() -> str:
    steps = [("upload","📤","Upload"),("extract","🔊","Extract"),
             ("transcribe","🧠","Transcribe"),("subtitle","📝","Subtitles"),
             ("burn","🔥","Burn")]
    done  = sum(1 for k,_,_ in steps if st.session_state.steps[k])
    act_i = done if done < len(steps) else -1
    html  = '<div class="pipeline">'
    for i,(key,icon,lbl) in enumerate(steps):
        if st.session_state.steps[key]:
            cls, ico = "pipe-done",   "✓"
        elif i == act_i:
            cls, ico = "pipe-active",  icon
        else:
            cls, ico = "pipe-pending", icon
        html += f'<div class="pipe-step {cls}"><div class="pipe-icon">{ico}</div><div class="pipe-lbl">{lbl}</div></div>'
        if i < len(steps)-1:
            lc = "pipe-line-done" if st.session_state.steps[key] else ""
            html += f'<div class="pipe-line {lc}"></div>'
    return html + "</div>"


def _stats_html() -> str:
    s = st.session_state.stats
    if not s: return ""
    items = [(s.get("segments","—"),"Segments"),(s.get("words","—"),"Words"),
             (s.get("duration","—"),"Duration"),(s.get("proc_time","—"),"Processed in")]
    html = '<div class="stats-row">'
    for v,l in items:
        html += f'<div class="stat-card"><div class="stat-val">{v}</div><div class="stat-lbl">{l}</div></div>'
    return html + "</div>"


def _apply_style_from_preset(pid: str):
    p = PRESET_STYLES[pid]
    st.session_state.active_preset = pid
    for k in ["font_size","color","bg_color","bg_opacity",
              "border_style","stroke_color","stroke_width",
              "shadow","position","text_case"]:
        st.session_state[k] = p[k]


def _do_burn():
    """Trigger a burn with current session style settings."""
    return burn_subtitles_to_video(
        st.session_state.video_path,
        st.session_state.chunks,
        fontsize      = st.session_state.font_size,
        color         = st.session_state.color,
        bg_color      = st.session_state.bg_color,
        bg_opacity    = st.session_state.bg_opacity,
        border_style  = st.session_state.border_style,
        stroke_color  = st.session_state.stroke_color,
        stroke_width  = st.session_state.stroke_width,
        shadow        = st.session_state.shadow,
        position      = st.session_state.position,
        text_case     = st.session_state.text_case,
        session_id    = st.session_state.session_id,
    )


# ── Sidebar (navigation only) ─────────────────────────────────────────────────
with st.sidebar:
    # ── Brand ────────────────────────────────────────────────────────────────
    st.markdown("""
<div class="sb-brand">
  <div class="sb-logo">
    <div class="sb-logo-icon">🎬</div>
    <div class="sb-logo-name">Sublyze AI</div>
  </div>
  <div class="sb-logo-tag">Auto Subtitle Generator</div>
</div>
<div class="sb-nav-label">Menu</div>
""", unsafe_allow_html=True)

    # ── Nav buttons ───────────────────────────────────────────────────────────
    nav_items = [
        ("✂️ Editor",  "✂️",  "Editor",  "Create & style subtitles"),
        ("❓ FAQ",      "❓",  "FAQ",     "Common questions answered"),
        ("🔒 Privacy", "🔒", "Privacy", "How we handle your data"),
    ]
    for page_key, icon, label, desc in nav_items:
        is_active = st.session_state.page == page_key
        active_cls = "nav-item-active" if is_active else ""
        st.markdown(f'<div class="{active_cls}">', unsafe_allow_html=True)
        if st.button(
            f"{icon}  {label}",
            key=f"nav_{page_key}",
            use_container_width=True,
        ):
            st.session_state.page = page_key
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("<hr class='sb-divider'>", unsafe_allow_html=True)
    st.markdown('<div class="sb-version">v2.0 · Streamlit Cloud</div>', unsafe_allow_html=True)

page = st.session_state.page


# ── Privacy ───────────────────────────────────────────────────────────────────
if page == "🔒 Privacy":
    st.markdown("""
<style>
/* Privacy page extras */
.privacy-hero { text-align:center; padding:40px 0 28px; }
.privacy-hero-title {
    font-size:clamp(1.8rem,4vw,2.8rem); font-weight:900;
    background:linear-gradient(90deg,#667eea 0%,#a855f7 50%,#ec4899 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text; line-height:1.2; margin:0 0 10px;
}
.privacy-hero-sub { color:#7070a0 !important; font-size:1rem; }

.tldr-box {
    background:linear-gradient(135deg,rgba(102,126,234,.12),rgba(168,85,247,.08));
    border:1px solid rgba(102,126,234,.3); border-radius:18px;
    padding:28px 32px; margin:0 0 36px; position:relative;
}
.tldr-tag {
    display:inline-block; background:linear-gradient(135deg,#667eea,#a855f7);
    color:#fff; font-size:.72rem; font-weight:800; letter-spacing:.08em;
    padding:4px 12px; border-radius:100px; text-transform:uppercase; margin-bottom:12px;
}
.tldr-headline {
    font-size:1.5rem; font-weight:800; color:#e0e0ff !important; margin:0 0 8px;
}
.tldr-body { color:#9090b8 !important; font-size:.95rem; line-height:1.65; margin:0; }

.priv-section-title {
    font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.09em;
    color:#667eea !important; border-bottom:1px solid rgba(102,126,234,.2);
    padding-bottom:8px; margin:36px 0 16px;
}

.priv-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:14px; margin:0 0 10px; }
.priv-card {
    background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07);
    border-radius:16px; padding:22px 20px; transition:.2s;
}
.priv-card:hover { border-color:rgba(102,126,234,.3); transform:translateY(-2px); }
.priv-card-icon { font-size:1.8rem; margin-bottom:10px; }
.priv-card-title { font-size:.9rem; font-weight:700; color:#d0d0f0 !important; margin-bottom:6px; }
.priv-card-body  { font-size:.8rem; color:#5a5a80 !important; line-height:1.55; }

.priv-fact-row { display:flex; flex-direction:column; gap:10px; margin:0 0 8px; }
.priv-fact {
    display:flex; align-items:flex-start; gap:12px;
    background:rgba(255,255,255,.025); border:1px solid rgba(255,255,255,.05);
    border-radius:12px; padding:14px 16px;
}
.priv-fact-icon { font-size:1.2rem; flex-shrink:0; margin-top:1px; }
.priv-fact-text { font-size:.85rem; color:#8080a0 !important; line-height:1.5; }
.priv-fact-text b { color:#c0c0e0 !important; }

.tech-table { width:100%; border-collapse:collapse; margin:0 0 8px; }
.tech-table th {
    text-align:left; font-size:.65rem; text-transform:uppercase; letter-spacing:.08em;
    color:#505075 !important; padding:8px 12px; border-bottom:1px solid rgba(255,255,255,.07);
}
.tech-table td { padding:12px 12px; border-bottom:1px solid rgba(255,255,255,.04); font-size:.83rem; color:#9090b0 !important; }
.tech-table tr:last-child td { border-bottom:none; }
.tech-table td:first-child { color:#c0c0e0 !important; font-weight:600; }
.tech-badge {
    display:inline-block; padding:3px 9px; border-radius:6px; font-size:.7rem; font-weight:700;
    background:rgba(52,211,153,.12); border:1px solid rgba(52,211,153,.25); color:#6ee7b7 !important;
}

.no-badge {
    background:rgba(239,68,68,.1); border:1px solid rgba(239,68,68,.25); color:#f87171 !important;
    display:inline-block; padding:3px 9px; border-radius:6px; font-size:.7rem; font-weight:700;
}
</style>
""", unsafe_allow_html=True)

    # Hero
    st.markdown("""
<div class="privacy-hero">
  <div class="privacy-hero-title">🔐 Privacy Policy</div>
  <div class="privacy-hero-sub">Last updated · June 2025</div>
</div>
""", unsafe_allow_html=True)

    # TL;DR
    st.markdown("""
<div class="tldr-box">
  <div class="tldr-tag">tl;dr</div>
  <div class="tldr-headline">Your video stays yours. We never store it.</div>
  <p class="tldr-body">
    Sublyze AI processes your video <strong style="color:#c0c0e0">entirely on our server</strong> for the duration of your session —
    audio extraction, transcription, and subtitle burning all happen there.
    Once you close your session, every temporary file is discarded.
    We do <strong style="color:#c0c0e0">not</strong> sell your data, train models on your content, or share anything with third parties.
  </p>
</div>
""", unsafe_allow_html=True)

    # What happens to your file
    st.markdown('<div class="priv-section-title">What happens to your file</div>', unsafe_allow_html=True)
    st.markdown("""
<div class="priv-fact-row">
  <div class="priv-fact">
    <span class="priv-fact-icon">📤</span>
    <span class="priv-fact-text"><b>Upload</b> — your video is written to a temporary, session-scoped folder on the server. It is never indexed, logged by filename, or linked to your identity.</span>
  </div>
  <div class="priv-fact">
    <span class="priv-fact-icon">🔊</span>
    <span class="priv-fact-text"><b>Audio extraction</b> — FFmpeg strips a mono 16 kHz WAV track from your video. Only this audio file is fed to the transcription model — the original video is not read again.</span>
  </div>
  <div class="priv-fact">
    <span class="priv-fact-icon">🧠</span>
    <span class="priv-fact-text"><b>Transcription</b> — OpenAI Whisper runs <em>locally on our server</em>. Your audio is never sent to OpenAI's API or any external service. No API key, no cloud call.</span>
  </div>
  <div class="priv-fact">
    <span class="priv-fact-icon">🔥</span>
    <span class="priv-fact-text"><b>Subtitle burn</b> — FFmpeg re-encodes the video with subtitles burned in. The result is made available only to you via your browser session.</span>
  </div>
  <div class="priv-fact">
    <span class="priv-fact-icon">🗑️</span>
    <span class="priv-fact-text"><b>Cleanup</b> — all temporary files (WAV, SRT, burned MP4) are session-scoped and removed when no longer needed. Nothing is retained after your session ends.</span>
  </div>
</div>
""", unsafe_allow_html=True)

    # What we do NOT do
    st.markdown('<div class="priv-section-title">What we never do</div>', unsafe_allow_html=True)
    st.markdown("""
<div class="priv-grid">
  <div class="priv-card">
    <div class="priv-card-icon">🚫</div>
    <div class="priv-card-title">No storage</div>
    <div class="priv-card-body">We do not persist your videos, transcripts, or subtitles to any database or long-term storage.</div>
  </div>
  <div class="priv-card">
    <div class="priv-card-icon">🤐</div>
    <div class="priv-card-title">No sharing</div>
    <div class="priv-card-body">Your content is never sold to, shared with, or accessible by any third party.</div>
  </div>
  <div class="priv-card">
    <div class="priv-card-icon">🧬</div>
    <div class="priv-card-title">No model training</div>
    <div class="priv-card-body">Your audio and transcripts are never used to fine-tune, retrain, or improve any AI model.</div>
  </div>
  <div class="priv-card">
    <div class="priv-card-icon">🔍</div>
    <div class="priv-card-title">No tracking</div>
    <div class="priv-card-body">We do not track individual users, link sessions to identities, or build usage profiles.</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # Tech stack
    st.markdown('<div class="priv-section-title">Technology stack</div>', unsafe_allow_html=True)
    st.markdown("""
<table class="tech-table">
  <thead>
    <tr>
      <th>Component</th><th>Tool</th><th>Data leaves server?</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>🧠 Transcription</td>
      <td>OpenAI Whisper (open-source, self-hosted)</td>
      <td><span class="tech-badge">✓ Never</span></td>
    </tr>
    <tr>
      <td>🎬 Video processing</td>
      <td>FFmpeg · libass subtitle filter</td>
      <td><span class="tech-badge">✓ Never</span></td>
    </tr>
    <tr>
      <td>📝 Subtitle format</td>
      <td>SRT (open standard)</td>
      <td><span class="tech-badge">✓ Never</span></td>
    </tr>
    <tr>
      <td>🚀 Hosting</td>
      <td>Streamlit Cloud</td>
      <td><span class="tech-badge">✓ Server-local only</span></td>
    </tr>
  </tbody>
</table>
""", unsafe_allow_html=True)

    # Contact
    st.markdown('<div class="priv-section-title">Questions?</div>', unsafe_allow_html=True)
    st.markdown("""
<div class="priv-fact">
  <span class="priv-fact-icon">💬</span>
  <span class="priv-fact-text">
    If you have any privacy-related questions or concerns, open an issue or start a discussion on
    <a href="https://github.com/Sahil081997/sublyze-ai" target="_blank" style="color:#667eea;text-decoration:none">GitHub ↗</a>.
    We're committed to being transparent about how your data is handled.
  </span>
</div>
""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:48px'></div>", unsafe_allow_html=True)
    st.stop()


# ── FAQ ───────────────────────────────────────────────────────────────────────
if page == "❓ FAQ":
    st.markdown("""
<style>
.faq-hero { text-align:center; padding:40px 0 28px; }
.faq-hero-title {
    font-size:clamp(1.8rem,4vw,2.8rem); font-weight:900;
    background:linear-gradient(90deg,#667eea 0%,#a855f7 50%,#ec4899 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text; line-height:1.2; margin:0 0 10px;
}
.faq-hero-sub { color:#7070a0 !important; font-size:1rem; }

.faq-cat-label {
    font-size:.68rem; font-weight:700; text-transform:uppercase;
    letter-spacing:.1em; color:#667eea !important;
    border-bottom:1px solid rgba(102,126,234,.2);
    padding-bottom:8px; margin:32px 0 4px;
    display:flex; align-items:center; gap:8px;
}

/* Expander styling */
[data-testid="stExpander"] {
    background:rgba(255,255,255,.025) !important;
    border:1px solid rgba(255,255,255,.07) !important;
    border-radius:14px !important;
    margin-bottom:8px !important;
    overflow:hidden !important;
}
[data-testid="stExpander"]:hover {
    border-color:rgba(102,126,234,.3) !important;
}
[data-testid="stExpander"] summary {
    font-size:.93rem !important;
    font-weight:600 !important;
    color:#c8c8e8 !important;
    padding:14px 18px !important;
}
[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
    padding:0 18px 16px !important;
    color:#7878a0 !important;
    font-size:.88rem !important;
    line-height:1.65 !important;
    border-top:1px solid rgba(255,255,255,.05) !important;
}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="faq-hero">
  <div class="faq-hero-title">❓ Frequently Asked Questions</div>
  <div class="faq-hero-sub">Everything you need to know about Sublyze AI</div>
</div>
""", unsafe_allow_html=True)

    # ── About Sublyze ─────────────────────────────────────────────────────────
    st.markdown('<div class="faq-cat-label">🎬 About Sublyze AI</div>', unsafe_allow_html=True)

    with st.expander("What is Sublyze AI?"):
        st.markdown("""
Sublyze AI is a free, browser-accessible tool that automatically generates and burns subtitles into your videos.

You upload a video, our AI transcribes the speech, and you get back a fully subtitled MP4 — all in one click.
No account, no credit card, no software to install.
        """)

    with st.expander("Is Sublyze AI really free?"):
        st.markdown("""
Yes — completely free. There are no hidden tiers, watermarks, or paywalls.

Sublyze is powered by **OpenAI Whisper** (open-source) and **FFmpeg** (open-source).
The only cost is the server running the app, which is hosted on Streamlit Cloud.
        """)

    with st.expander("How is Sublyze different from other subtitle tools?"):
        st.markdown("""
Most online subtitle tools either:
- Require a paid subscription or add watermarks on the free tier
- Send your video to a third-party AI API (OpenAI, AssemblyAI, etc.)
- Only give you an SRT file — you have to burn it yourself

Sublyze does **all three steps in one**: transcribes with a self-hosted Whisper model,
lets you style the subtitles, and burns them directly into your video — all for free with no data leaving our server to any external AI service.
        """)

    with st.expander("Do I need to create an account?"):
        st.markdown("""
No account needed. Just open the app, upload your video, and go.
Each visit starts a fresh session — no login, no email, no sign-up.
        """)

    # ── How it works ──────────────────────────────────────────────────────────
    st.markdown('<div class="faq-cat-label">⚙️ How It Works</div>', unsafe_allow_html=True)

    with st.expander("What video formats are supported?"):
        st.markdown("""
Currently **MP4** and **MOV** are supported, up to **200 MB** in size.

These cover the vast majority of videos from phones, cameras, and screen recorders.
Support for additional formats (MKV, WebM, AVI) may be added in a future update.
        """)

    with st.expander("How long does processing take?"):
        st.markdown("""
It depends on the length of your video:

| Video length | Approx. time |
|---|---|
| < 2 minutes | ~15–30 seconds |
| 2–10 minutes | ~30–90 seconds |
| 10–30 minutes | ~2–5 minutes |

The first run may take slightly longer as the Whisper model warms up.
        """)

    with st.expander("What languages are supported?"):
        st.markdown("""
Whisper supports **99 languages** including English, Spanish, French, German, Hindi,
Portuguese, Arabic, Chinese, Japanese, Korean, and many more.

Language is detected **automatically** — you don't need to set it manually.
        """)

    with st.expander("How accurate is the transcription?"):
        st.markdown("""
Sublyze uses **Whisper small**, which delivers strong accuracy for clear speech in a quiet environment.

Accuracy may be lower for:
- Heavy accents or very fast speech
- Multiple overlapping speakers
- Low audio quality or heavy background noise

For professional use cases needing higher accuracy, upgrading to Whisper `medium` or `large` would improve results.
        """)

    # ── Subtitles & Styling ────────────────────────────────────────────────────
    st.markdown('<div class="faq-cat-label">✏️ Subtitles & Styling</div>', unsafe_allow_html=True)

    with st.expander("Can I edit the subtitles before burning?"):
        st.markdown("""
Yes! After transcription, scroll down to the **Edit Subtitles** expander.

You can:
- Edit the text of any segment directly
- Merge short segments into longer, more readable lines
- Click **Re-burn with Edits** to apply your changes to the video
        """)

    with st.expander("What subtitle styles are available?"):
        st.markdown("""
Sublyze includes **6 one-click preset styles**:

| Style | Look |
|---|---|
| 🎬 Subtle | Semi-transparent box — Netflix / YouTube style |
| 💥 Bold | Thick stroke, all-caps — TikTok / Shorts |
| 🎥 Cinematic | Thin outline, no background — classic film |
| ✨ Neon | Bold yellow on dark — social media pop |
| 📰 News | Solid black block — broadcast style |
| 🤍 Minimal | Drop shadow only — clean, no background |

You can also fully customize font size, text color, background, stroke, shadow, and position.
        """)

    with st.expander("Can I download just the .SRT subtitle file?"):
        st.markdown("""
Yes. After processing, use the **📄 SRT** download button to get a standard `.srt` file.

This file can be imported into any video editor (Premiere Pro, DaVinci Resolve, CapCut)
or uploaded directly to YouTube, Vimeo, or any video platform that accepts subtitle tracks.
        """)

    with st.expander("Can I reposition the subtitles?"):
        st.markdown("""
Yes — open the **Shadow & Position** panel and choose **Bottom**, **Center**, or **Top**.

Bottom is the default and most widely used position for readability.
        """)

    # ── Privacy & Data ─────────────────────────────────────────────────────────
    st.markdown('<div class="faq-cat-label">🔒 Privacy & Data</div>', unsafe_allow_html=True)

    with st.expander("Is my video stored on your servers?"):
        st.markdown("""
No. Your video is held in a **temporary session folder** only for the duration of processing.
Once your session ends, all files (video, WAV audio, SRT, burned MP4) are discarded.

We do not store, log, or archive any user videos. See the [Privacy page](#) for full details.
        """)

    with st.expander("Do you use my video or transcript to train AI models?"):
        st.markdown("""
**Never.** Your audio and transcripts are not used to fine-tune, retrain, or improve any AI model —
including Whisper. The model runs inference only; your data is input, not training material.
        """)

    with st.expander("Does Sublyze send my video to OpenAI or any external API?"):
        st.markdown("""
No. Whisper runs **locally on our server** — it is the open-source model, not the OpenAI API.
Your audio never leaves our infrastructure and is never transmitted to OpenAI, Google, or any other third party.
        """)

    st.markdown("<div style='margin-top:48px'></div>", unsafe_allow_html=True)
    st.stop()
st.markdown("""
<div style="padding:20px 0 6px">
  <div class="hero-title">Sublyze AI</div>
  <div class="hero-sub">Auto-generate burned-in subtitles for any video — free, in one click.</div>
</div>
<div class="badge-row">
  <span class="badge badge-green">✅ 100% Free</span>
  <span class="badge badge-purple">🌍 99 Languages</span>
  <span class="badge badge-blue">⚡ No Account Needed</span>
  <span class="badge badge-pink">📥 Download MP4 + SRT</span>
</div>""", unsafe_allow_html=True)

if not st.session_state.steps["upload"]:
    st.markdown("""
<div class="feat-grid">
  <div class="feat-card"><div class="feat-icon">🧠</div><div class="feat-name">AI Transcription</div><div class="feat-desc">OpenAI Whisper detects speech across 90+ languages — no API key needed.</div></div>
  <div class="feat-card"><div class="feat-icon">🎨</div><div class="feat-name">6 Preset Styles</div><div class="feat-desc">Subtle, Bold, Cinematic, Neon, News, Minimal — one click to apply.</div></div>
  <div class="feat-card"><div class="feat-icon">✏️</div><div class="feat-name">Full Style Control</div><div class="feat-desc">Font size, colors, stroke, shadow, position, text case — all customizable.</div></div>
  <div class="feat-card"><div class="feat-icon">📥</div><div class="feat-name">Export Anywhere</div><div class="feat-desc">Download subtitled MP4 or .SRT file for any video editor or player.</div></div>
</div>""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "📤 Drop your video here or click to browse",
    type=SUPPORTED_FORMATS,
    help=f"Supported: MP4, MOV · Max {MAX_FILE_MB} MB",
    key=f"uploader_{st.session_state.session_id}",
)

pipeline_ph = st.empty()
if any(st.session_state.steps.values()):
    pipeline_ph.markdown(_pipeline_html(), unsafe_allow_html=True)

# ── Processing pipeline ───────────────────────────────────────────────────────
if uploaded_file and not st.session_state.steps["upload"]:
    file_ext = os.path.splitext(uploaded_file.name)[-1][1:].lower()
    file_mb  = uploaded_file.size / (1024*1024)
    if file_ext not in SUPPORTED_FORMATS:
        st.error("❌ Unsupported format. Please upload MP4 or MOV."); st.stop()
    if file_mb > MAX_FILE_MB:
        st.error(f"❌ File too large ({file_mb:.1f} MB). Max {MAX_FILE_MB} MB."); st.stop()

    t_start = time.time()
    pipeline_ph.markdown(_pipeline_html(), unsafe_allow_html=True)

    video_path = save_uploaded_file(uploaded_file)
    st.session_state.video_path = video_path
    st.session_state.steps["upload"] = True
    pipeline_ph.markdown(_pipeline_html(), unsafe_allow_html=True)

    with st.spinner("🔊 Extracting audio…"):
        audio_path = extract_audio(video_path)
        st.session_state.audio_path = audio_path
        st.session_state.steps["extract"] = True
    pipeline_ph.markdown(_pipeline_html(), unsafe_allow_html=True)

    with st.spinner("🧠 Transcribing with Whisper AI… (30–60 s on first run)"):
        transcript, chunks = transcribe_audio(audio_path)

    if not transcript.strip():
        st.error("❌ No speech detected. Please upload a video with spoken audio.")
        if st.button("🔁 Try a Different Video"):
            st.session_state.clear(); st.rerun()
        st.stop()

    # Auto-merge very short segments for readable subtitles
    chunks = merge_short_segments(chunks, min_duration=1.5, min_words=2)
    st.session_state.transcript = transcript
    st.session_state.chunks     = chunks
    st.session_state.steps["transcribe"] = True

    dur_s = chunks[-1]["timestamp"][1] if chunks else 0
    st.session_state.stats = {
        "segments":  len(chunks),
        "words":     len(transcript.split()),
        "duration":  fmt_dur(dur_s),
        "proc_time": "",
    }
    pipeline_ph.markdown(_pipeline_html(), unsafe_allow_html=True)

    with st.spinner("📝 Generating subtitle file…"):
        os.makedirs("data", exist_ok=True)
        srt_text = generate_srt(chunks, text_case=st.session_state.text_case)
        srt_path = save_srt(srt_text, f"data/subtitles_{st.session_state.session_id}.srt")
        st.session_state.srt_path    = srt_path
        st.session_state.srt_content = srt_text
        st.session_state.steps["subtitle"] = True
    pipeline_ph.markdown(_pipeline_html(), unsafe_allow_html=True)

    with st.spinner("🔥 Burning subtitles into video…"):
        try:
            burned = _do_burn()
            st.session_state.burned_video_path = burned
            st.session_state.steps["burn"] = True
        except Exception as err:
            st.error(f"⚠️ Burn failed: {err}\n\nYou can still download the .SRT file.")
    pipeline_ph.markdown(_pipeline_html(), unsafe_allow_html=True)

    elapsed = time.time() - t_start
    st.session_state.stats["proc_time"] = f"{elapsed:.0f} s"
    if st.session_state.steps["burn"]:
        st.success(f"✅ Done in **{elapsed:.1f} s** — your subtitled video is ready!")
    else:
        st.warning("⚠️ Burning failed — subtitle file (.SRT) is still available below.")


# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.steps["burn"] and st.session_state.burned_video_path:

    sh = _stats_html()
    if sh: st.markdown(sh, unsafe_allow_html=True)

    # Two-column layout: Style panel | Video
    col_style, col_video = st.columns([2, 3], gap="large")

    # ── LEFT: Style panel ─────────────────────────────────────────────────────
    with col_style:
        st.markdown("### 🎨 Subtitle Style")

        # Preset gallery
        st.markdown('<div class="style-section">Quick Presets</div>', unsafe_allow_html=True)
        preset_ids = list(PRESET_STYLES.keys())
        p_cols = st.columns(3)
        for i, pid in enumerate(preset_ids):
            p = PRESET_STYLES[pid]
            is_active = st.session_state.active_preset == pid
            border = "2px solid #667eea" if is_active else "2px solid rgba(255,255,255,0.08)"
            bg     = "rgba(102,126,234,0.14)" if is_active else "rgba(255,255,255,0.03)"
            with p_cols[i % 3]:
                st.markdown(
                    f"<div style='background:{bg};border:{border};border-radius:12px;"
                    f"padding:10px 6px;text-align:center;margin-bottom:4px'>"
                    f"<div style='font-size:1.3rem'>{p['emoji']}</div>"
                    f"<div style='font-size:.72rem;font-weight:700;color:#c0c0e0;margin-top:4px'>{p['label']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if st.button(f"Apply", key=f"preset_{pid}", use_container_width=True):
                    _apply_style_from_preset(pid)
                    with st.spinner(f"Applying {p['label']} style…"):
                        try:
                            burned = _do_burn()
                            st.session_state.burned_video_path = burned
                            st.session_state.srt_content = generate_srt(
                                st.session_state.chunks,
                                text_case=st.session_state.text_case,
                            )
                            st.rerun()
                        except Exception as err:
                            st.error(f"Burn failed: {err}")

        # ── Font & Text ───────────────────────────────────────────────────────
        with st.expander("✏️  Font & Text", expanded=False):
            font_size  = st.slider("Size", 10, 48, st.session_state.font_size, key="sl_fs")
            text_case  = st.radio(
                "Case",
                ["original","upper","lower"],
                index=["original","upper","lower"].index(st.session_state.text_case),
                horizontal=True, key="rd_tc",
                format_func=lambda x: {"original":"Aa Original","upper":"AA UPPER","lower":"aa lower"}[x],
            )

        # ── Colors ────────────────────────────────────────────────────────────
        with st.expander("🎨  Colors & Background", expanded=True):
            color      = st.color_picker("Text color",       st.session_state.color,    key="cp_tc")
            bstyle_opt = st.radio(
                "Background",
                ["box","outline","none"],
                index=["box","outline","none"].index(st.session_state.border_style),
                horizontal=True, key="rd_bs",
                format_func=lambda x: {"box":"📦 Box","outline":"🖊 Outline","none":"🚫 None"}[x],
            )
            bg_color, bg_opacity, stroke_color, stroke_width = (
                st.session_state.bg_color, st.session_state.bg_opacity,
                st.session_state.stroke_color, st.session_state.stroke_width,
            )
            if bstyle_opt == "box":
                bg_color   = st.color_picker("Box color",    st.session_state.bg_color,    key="cp_bc")
                bg_opacity = st.slider("Box opacity", 0.0, 1.0, st.session_state.bg_opacity, step=0.05, key="sl_bo")
            elif bstyle_opt == "outline":
                stroke_color = st.color_picker("Stroke color", st.session_state.stroke_color, key="cp_sc")
                stroke_width = st.slider("Stroke width", 0, 8, st.session_state.stroke_width, key="sl_sw")

        # ── Shadow & Position ─────────────────────────────────────────────────
        with st.expander("🔆  Shadow & Position", expanded=False):
            shadow   = st.slider("Shadow depth", 0, 5, st.session_state.shadow, key="sl_sh")
            position = st.radio(
                "Position",
                ["bottom","center","top"],
                index=["bottom","center","top"].index(st.session_state.position),
                horizontal=True, key="rd_pos",
                format_func=lambda x: {"bottom":"⬇ Bottom","center":"↔ Center","top":"⬆ Top"}[x],
            )

        # Live preview box
        pr_rgb  = tuple(int(bg_color.lstrip("#")[i:i+2],16) for i in (0,2,4))
        pr_rgba = f"rgba({pr_rgb[0]},{pr_rgb[1]},{pr_rgb[2]},{bg_opacity})" if bstyle_opt=="box" else "transparent"
        pr_outline = f"2px solid {stroke_color}" if bstyle_opt=="outline" else "none"
        preview_text = {"original":"Sample subtitle text","upper":"SAMPLE SUBTITLE TEXT","lower":"sample subtitle text"}[text_case]
        st.markdown(
            f"<div style='margin-top:10px;padding:10px 16px;border-radius:10px;"
            f"background:{pr_rgba};color:{color};font-size:{font_size}px;"
            f"text-align:center;font-weight:700;outline:{pr_outline};'>"
            f"{preview_text}</div>",
            unsafe_allow_html=True,
        )

        # Apply button (only if user changed something manually)
        changed = (
            font_size   != st.session_state.font_size   or
            text_case   != st.session_state.text_case   or
            color       != st.session_state.color       or
            bstyle_opt  != st.session_state.border_style or
            bg_color    != st.session_state.bg_color    or
            bg_opacity  != st.session_state.bg_opacity  or
            stroke_color!= st.session_state.stroke_color or
            stroke_width!= st.session_state.stroke_width or
            shadow      != st.session_state.shadow      or
            position    != st.session_state.position
        )
        if changed:
            if st.button("🔥 Apply & Re-burn", use_container_width=True, key="apply_custom"):
                st.session_state.font_size    = font_size
                st.session_state.text_case    = text_case
                st.session_state.color        = color
                st.session_state.border_style = bstyle_opt
                st.session_state.bg_color     = bg_color
                st.session_state.bg_opacity   = bg_opacity
                st.session_state.stroke_color = stroke_color
                st.session_state.stroke_width = stroke_width
                st.session_state.shadow       = shadow
                st.session_state.position     = position
                st.session_state.active_preset = "custom"
                with st.spinner("Burning with custom style…"):
                    try:
                        burned = _do_burn()
                        st.session_state.burned_video_path = burned
                        st.rerun()
                    except Exception as err:
                        st.error(f"Burn failed: {err}")

    # ── RIGHT: Video ──────────────────────────────────────────────────────────
    with col_video:
        st.markdown("### 🎬 Preview")
        st.video(st.session_state.burned_video_path, format="video/mp4")

        dl_a, dl_b, dl_c = st.columns(3)
        with dl_a:
            with open(st.session_state.burned_video_path, "rb") as f:
                st.download_button("📥 Video", f, file_name="sublyze_output.mp4",
                                   mime="video/mp4", key="dl_vid", use_container_width=True)
        with dl_b:
            if st.session_state.srt_content:
                st.download_button("📄 SRT", st.session_state.srt_content,
                                   file_name="sublyze_subtitles.srt", mime="text/plain",
                                   key="dl_srt", use_container_width=True)
        with dl_c:
            if st.button("🔄 New Video", key="start_over", use_container_width=True):
                st.session_state.clear(); st.rerun()

    # ── Subtitle Editor (full-width, below) ───────────────────────────────────
    st.markdown("---")
    with st.expander("✏️  Edit Subtitles  ·  " +
                     f"{len(st.session_state.chunks)} segments", expanded=False):

        top_l, top_r = st.columns([3,1])
        with top_r:
            if st.button("🔀 Merge Short Segments", use_container_width=True, key="merge_btn"):
                merged = merge_short_segments(
                    st.session_state.chunks, min_duration=2.0, min_words=3
                )
                if len(merged) < len(st.session_state.chunks):
                    st.session_state.chunks = merged
                    st.session_state.srt_content = generate_srt(
                        merged, text_case=st.session_state.text_case
                    )
                    st.success(f"Merged to {len(merged)} segments — re-burn to apply.")
                    st.rerun()
                else:
                    st.info("No short segments to merge.")
        with top_l:
            st.markdown(
                "<small style='color:#505075'>Edit any segment below, then click "
                "<b>Re-burn with Edits</b>. "
                "🟢 = good length  🟡 = short  🔴 = very short</small>",
                unsafe_allow_html=True,
            )

        updated_chunks, edited = [], False
        for i, chunk in enumerate(st.session_state.chunks):
            s, e   = chunk["timestamp"]
            dur    = e - s
            dur_cls = "seg-dur-ok" if dur >= 1.5 else ("seg-dur-short" if dur >= 0.8 else "seg-dur-vshort")
            chars  = len(chunk["text"])

            st.markdown(
                f"<div class='seg-header'>"
                f"<span class='seg-num'>#{i+1}</span>"
                f"<span class='seg-time'>{fmt_dur(s)} → {fmt_dur(e)}</span>"
                f"<span class='seg-dur {dur_cls}'>{dur:.1f}s</span>"
                f"<span class='seg-chars'>{chars} chars</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            new_text = st.text_area(
                label=" ", value=chunk["text"], height=60,
                key=f"seg_{i}_{st.session_state.session_id}",
                label_visibility="collapsed",
            )
            if new_text.strip() != chunk["text"].strip():
                edited = True
            updated_chunks.append({"timestamp": chunk["timestamp"], "text": new_text.strip()})
            if i < len(st.session_state.chunks)-1:
                st.markdown("<hr style='border-color:rgba(255,255,255,0.04);margin:4px 0'>",
                            unsafe_allow_html=True)

        if edited:
            st.markdown("---")
            if st.button("🔥 Re-burn with Edits", key="reburn_edits", use_container_width=False):
                with st.spinner("Re-burning with edited subtitles…"):
                    try:
                        st.session_state.chunks      = updated_chunks
                        st.session_state.srt_content = generate_srt(
                            updated_chunks, text_case=st.session_state.text_case
                        )
                        burned = _do_burn()
                        st.session_state.burned_video_path = burned
                        st.success("✅ Video updated!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Re-burn failed: {err}")

elif st.session_state.steps["subtitle"] and not st.session_state.steps["burn"]:
    if st.session_state.srt_content:
        st.download_button("📄 Download Subtitles (.SRT)", st.session_state.srt_content,
                           file_name="sublyze_subtitles.srt", key="dl_srt_fallback")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
  Built with ❤️ using
  <a href="https://openai.com/research/whisper" target="_blank">OpenAI Whisper</a>,
  <a href="https://ffmpeg.org" target="_blank">FFmpeg</a> &amp;
  <a href="https://streamlit.io" target="_blank">Streamlit</a> ·
  <a href="https://github.com/Sahil081997/sublyze-ai" target="_blank">⭐ GitHub</a>
</div>""", unsafe_allow_html=True)
