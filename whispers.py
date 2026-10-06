import os
import tempfile
import imageio_ffmpeg  # Helps resolve ffmpeg path automatically
import streamlit as st
import whisper

# Set ffmpeg path dynamically for Windows
try:
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(ffmpeg_exe)
    os.environ["PATH"] += os.pathsep + ffmpeg_dir
except Exception:
    pass

# ==========================================
# 1. STREAMLIT CONFIG & OCEAN THEME CSS
# ==========================================
st.set_page_config(
    page_title="Whispers — Audio Transcriber",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

OCEAN_CSS = """
<style>
/* App background - Deep Abyssal Ocean */
.stApp {
    background: linear-gradient(135deg, #0b192c 0%, #1e3e62 50%, #001f3f 100%);
    color: #f0f8ff;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: rgba(11, 25, 44, 0.85);
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(0, 210, 255, 0.2);
}

/* Main title styling */
.ocean-header {
    background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 50%, #00f2fe 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3rem;
    font-weight: 800;
    margin-bottom: 0.2rem;
    letter-spacing: -1px;
}

.ocean-subtitle {
    color: #a8dadc;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

/* Cards & Containers */
.ocean-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 1.5rem;
    border: 1px solid rgba(0, 212, 255, 0.25);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    margin-bottom: 1.5rem;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #00b4db 0%, #0083b0 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.6rem 1.8rem !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 15px rgba(0, 180, 219, 0.4) !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0, 242, 254, 0.6) !important;
}

/* Text area & selectbox styling */
textarea, select {
    background-color: rgba(15, 32, 67, 0.8) !important;
    color: #e0f7fa !important;
    border: 1px solid #00b4db !important;
    border-radius: 10px !important;
}

/* Wave Divider */
.wave-line {
    height: 4px;
    background: linear-gradient(90deg, transparent, #00d2ff, #00f2fe, transparent);
    border-radius: 2px;
    margin: 1.5rem 0;
}
</style>
"""

st.markdown(OCEAN_CSS, unsafe_allow_html=True)


# ==========================================
# 2. MODEL LOADING (CACHED)
# ==========================================
@st.cache_resource
def load_whisper_model(model_size: str):
    """Loads OpenAI Whisper model into memory."""
    return whisper.load_model(model_size)


# ==========================================
# 3. SIDEBAR & SETTINGS
# ==========================================
with st.sidebar:
    st.markdown("## 🌊 **Whispers Settings**")
    st.markdown("---")

    model_size = st.selectbox(
        "Select Whisper Model:",
        options=["tiny", "base", "small", "medium"],
        index=1,
        help="'base' or 'small' is recommended for optimal accuracy and speed on CPU.",
    )

    language_choice = st.selectbox(
        "Primary Language / Auto:",
        options=["Auto-Detect", "Swahili (sw)", "English (en)"],
        index=0,
    )

    st.markdown("---")
    st.markdown(
        "**Supported Languages:**\n"
        "• 🇰🇪 / 🇹🇿 Swahili (`sw`)\n"
        "• 🇬🇧 / 🇺🇸 English (`en`)\n"
        "• 🌍 Code-Switching (Sheng/Mix)"
    )


# ==========================================
# 4. MAIN INTERFACE
# ==========================================
st.markdown('<div class="ocean-header">🌊 Whispers</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="ocean-subtitle">Multilingual Swahili & English Audio Transcription Agent</div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="wave-line"></div>', unsafe_allow_html=True)

# Tabs for Record vs Upload
tab1, tab2 = st.tabs(["🎙️ Record Spoken Audio", "📁 Upload Audio File"])

audio_bytes = None
file_extension = "wav"

with tab1:
    st.markdown("#### Tap below to record your voice:")
    recorded_audio = st.audio_input("Record audio directly from microphone")
    if recorded_audio:
        audio_bytes = recorded_audio.read()

with tab2:
    st.markdown("#### Choose an existing audio file:")
    uploaded_file = st.file_uploader(
        "Supported formats: WAV, MP3, M4A, OGG, FLAC",
        type=["wav", "mp3", "m4a", "ogg", "flac"],
    )
    if uploaded_file is not None:
        audio_bytes = uploaded_file.read()
        file_extension = uploaded_file.name.split(".")[-1]
        st.audio(audio_bytes, format=f"audio/{file_extension}")

st.markdown('<div class="wave-line"></div>', unsafe_allow_html=True)

# ==========================================
# 5. TRANSCRIPTION LOGIC
# ==========================================
if audio_bytes:
    if st.button("✨ Transcribe with Whispers", type="primary"):
        with st.spinner("🌊 Submerging into audio... Transcribing Swahili / English..."):
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{file_extension}"
            ) as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name

            try:
                model = load_whisper_model(model_size)

                options = {}
                if language_choice == "Swahili (sw)":
                    options["language"] = "sw"
                elif language_choice == "English (en)":
                    options["language"] = "en"

                result = model.transcribe(tmp_path, fp16=False, **options)

                transcription_result = result.get("text", "").strip()
                detected_lang = result.get("language", "auto").upper()

                st.markdown(
                    f"""
                    <div class="ocean-card">
                        <h3 style="color: #00f2fe; margin-top: 0;">📜 Transcription Output</h3>
                        <p style="color: #a8dadc; font-size: 0.9rem;">
                            Detected Language: <b>{detected_lang}</b>
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.text_area(
                    "Full Transcript:",
                    value=transcription_result,
                    height=180,
                )

                # Segment timestamps
                segments = result.get("segments", [])
                if segments:
                    segment_data = [
                        {
                            "Start (s)": round(seg["start"], 2),
                            "End (s)": round(seg["end"], 2),
                            "Text": seg["text"],
                        }
                        for seg in segments
                    ]
                    with st.expander("⏱️ View Segment Timestamps"):
                        st.dataframe(
                            segment_data, use_container_width=True, hide_index=True
                        )

                st.download_button(
                    label="📥 Download Transcript (.txt)",
                    data=transcription_result,
                    file_name="whispers_transcript.txt",
                    mime="text/plain",
                )

            except Exception as e:
                st.error(f"Error processing audio: {str(e)}")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)