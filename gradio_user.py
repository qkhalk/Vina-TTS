import gradio as gr
import soundfile as sf
import tempfile
import torch
import os
import time
import numpy as np
from typing import Generator, Optional, Tuple
import yaml
from model_manager import ModelManager, ModelStatus
from auth import UserManager, SessionManager, UserRole
from utils.core_utils import split_text_into_chunks
from functools import lru_cache


# Load configuration
CONFIG_PATH = "config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    _config = yaml.safe_load(f) or {}

VOICE_SAMPLES = _config.get("voice_samples", {})
_text_settings = _config.get("text_settings", {})
MAX_CHARS_PER_CHUNK = _text_settings.get("max_chars_per_chunk", 256)

# Initialize managers
model_manager = ModelManager.get_instance()
user_manager = UserManager()
session_manager = SessionManager()


@lru_cache(maxsize=32)
def get_ref_text_cached(text_path: str) -> str:
    """Cache reference text loading"""
    with open(text_path, "r", encoding="utf-8") as f:
        return f.read()


def recover_user_session():
    """Recover user session from localStorage on page load."""
    return """
    function() {
        const token = localStorage.getItem('vieneu_user_session') || '';
        console.log('Recovering user session:', token ? 'Token found' : 'No token');
        return token;
    }
    """


def user_login(username: str, password: str):
    """Handle user login."""
    if user_manager.verify_user(username, password):
        token = session_manager.create_session(username, UserRole.USER)
        return (
            gr.update(visible=False),  # Hide login
            gr.update(visible=True),   # Show TTS interface
            token,
            ""
        )
    else:
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            "",
            "❌ Invalid username or password"
        )


def validate_and_restore_user_session(token):
    """Validate token and restore TTS interface."""
    access_enabled = user_manager.is_access_enabled()
    available_voices = get_available_voices()
    
    if not access_enabled:
        # Access protection disabled - show TTS interface
        return (
            gr.update(visible=False),  # Hide login
            gr.update(visible=True),   # Show TTS
            token,                     # Keep token (might be empty)
            "",                        # Clear login status
            get_model_status_text(),   # Model status
            gr.update(choices=available_voices, value=available_voices[0] if available_voices else None)  # Voice dropdown
        )
    
    if not token or not validate_user_session(token):
        # Invalid session - show login
        return (
            gr.update(visible=True),   # Show login
            gr.update(visible=False),  # Hide TTS
            "",                        # Clear token
            "",                        # Clear login status
            get_model_status_text(),   # Model status
            gr.update(choices=available_voices, value=available_voices[0] if available_voices else None)  # Voice dropdown
        )
    else:
        # Valid session - show TTS
        return (
            gr.update(visible=False),  # Hide login
            gr.update(visible=True),   # Show TTS
            token,                     # Keep token
            "",                        # Clear login status
            get_model_status_text(),   # Model status
            gr.update(choices=available_voices, value=available_voices[0] if available_voices else None)  # Voice dropdown
        )


def validate_user_session(token: str):
    """Validate user session token."""
    # If access protection is disabled, always allow
    if not user_manager.is_access_enabled():
        return True
    
    if not token:
        return False
    
    session = session_manager.validate_session(token)
    return session is not None


def check_model_ready():
    """Check if model is loaded and ready."""
    status = model_manager.get_status()
    return status["status"] == ModelStatus.LOADED


def get_model_status_text():
    """Get user-friendly model status text."""
    status = model_manager.get_status()
    
    if status["status"] == ModelStatus.LOADED:
        return "✅ Model Ready"
    elif status["status"] == ModelStatus.LOADING:
        return "⏳ Model Loading..."
    elif status["status"] == ModelStatus.ERROR:
        return f"❌ Model Error: {status.get('error', 'Unknown error')}"
    else:
        return "⚠️ Model Not Loaded"


def get_available_voices():
    """Get list of available voices based on loaded model configuration."""
    all_voices = list(VOICE_SAMPLES.keys())
    supported_voices = model_manager.get_supported_voices(all_voices)
    
    # If model not loaded or no filtering needed, return all voices
    if not supported_voices:
        return all_voices
    
    return supported_voices


def synthesize_tts(token, text, voice_choice, custom_audio, custom_text, mode_tab, use_batch):
    """User TTS synthesis."""
    if not validate_user_session(token):
        yield None, "❌ Unauthorized. Please login."
        return
    
    if not check_model_ready():
        yield None, "⚠️ Model is not loaded. Please contact administrator."
        return
    
    if not text or text.strip() == "":
        yield None, "⚠️ Please enter text to synthesize"
        return
    
    raw_text = text.strip()
    tts = model_manager.get_model()
    
    if tts is None:
        yield None, "❌ Model not available"
        return
    
    # Setup Reference
    if mode_tab == "custom_mode":
        if custom_audio is None or not custom_text:
            yield None, "⚠️ Please provide reference audio and text"
            return
        ref_audio_path = custom_audio
        ref_text_raw = custom_text
        ref_codes_path = None
    else:
        if voice_choice not in VOICE_SAMPLES:
            yield None, "⚠️ Please select a voice"
            return
        ref_audio_path = VOICE_SAMPLES[voice_choice]["audio"]
        text_path = VOICE_SAMPLES[voice_choice]["text"]
        ref_codes_path = VOICE_SAMPLES[voice_choice]["codes"]
        
        if not os.path.exists(ref_audio_path):
            yield None, "❌ Reference audio not found"
            return
        
        ref_text_raw = get_ref_text_cached(text_path)
    
    yield None, "📄 Processing reference..."
    
    # Encode or load reference
    try:
        status_info = model_manager.get_status()
        config = status_info.get('config', {})
        codec_repo = config.get('codec_repo', '')
        use_preencoded = 'onnx' in codec_repo.lower()
        
        if use_preencoded and ref_codes_path and os.path.exists(ref_codes_path):
            ref_codes = torch.load(ref_codes_path, map_location="cpu", weights_only=True)
        else:
            # Use cached reference if available (LMDeploy/FastVieNeuTTS)
            if model_manager.using_lmdeploy and hasattr(tts, 'get_cached_reference') and mode_tab == "preset_mode":
                ref_codes = tts.get_cached_reference(voice_choice, ref_audio_path, ref_text_raw)
            else:
                ref_codes = tts.encode_reference(ref_audio_path)
        
        if isinstance(ref_codes, torch.Tensor):
            ref_codes = ref_codes.cpu().numpy()
    except Exception as e:
        yield None, f"❌ Error processing reference: {e}"
        return
    
    # Split text into chunks
    text_chunks = split_text_into_chunks(raw_text, max_chars=MAX_CHARS_PER_CHUNK)
    total_chunks = len(text_chunks)
    
    backend_name = "LMDeploy" if model_manager.using_lmdeploy else "Standard"
    batch_info = " (Batch)" if use_batch and model_manager.using_lmdeploy and total_chunks > 1 else ""
    
    yield None, f"🚀 Synthesizing {backend_name}{batch_info} ({total_chunks} chunks)..."
    
    all_audio_segments = []
    sr = 24000
    silence_pad = np.zeros(int(sr * 0.15), dtype=np.float32)
    
    start_time = time.time()
    
    try:
        # Use batch processing if available and enabled
        if use_batch and model_manager.using_lmdeploy and hasattr(tts, 'infer_batch') and total_chunks > 1:
            chunk_wavs = tts.infer_batch(text_chunks, ref_codes, ref_text_raw)
            
            for i, chunk_wav in enumerate(chunk_wavs):
                if chunk_wav is not None and len(chunk_wav) > 0:
                    all_audio_segments.append(chunk_wav)
                    if i < total_chunks - 1:
                        all_audio_segments.append(silence_pad)
        else:
            # Sequential processing
            for i, chunk in enumerate(text_chunks):
                yield None, f"⏳ Processing chunk {i+1}/{total_chunks}..."
                
                chunk_wav = tts.infer(chunk, ref_codes, ref_text_raw)
                
                if chunk_wav is not None and len(chunk_wav) > 0:
                    all_audio_segments.append(chunk_wav)
                    if i < total_chunks - 1:
                        all_audio_segments.append(silence_pad)
        
        if not all_audio_segments:
            yield None, "❌ Failed to generate audio"
            return
        
        yield None, "💾 Saving audio..."
        
        final_wav = np.concatenate(all_audio_segments)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            sf.write(tmp.name, final_wav, sr)
            output_path = tmp.name
        
        process_time = time.time() - start_time
        speed_info = f", Speed: {len(final_wav)/sr/process_time:.2f}x realtime" if process_time > 0 else ""
        
        yield output_path, f"✅ Complete! (Time: {process_time:.2f}s{speed_info})"
        
    except Exception as e:
        yield None, f"❌ Error: {str(e)}"


def create_user_interface():
    """Create user Gradio interface."""
    
    with gr.Blocks(title="VieNeu-TTS", js=recover_user_session()) as user_interface:
        session_token = gr.State("")
        
        # Check if access protection is enabled
        access_enabled = user_manager.is_access_enabled()
        
        # Login page (visible if access protection enabled)
        with gr.Column(visible=access_enabled) as login_page:
            gr.Markdown("# 🔐 User Login")
            gr.Markdown("Please login to access VieNeu-TTS")
            username_input = gr.Textbox(label="Username", placeholder="Enter your username")
            password_input = gr.Textbox(label="Password", type="password", placeholder="Enter your password")
            login_btn = gr.Button("Login", variant="primary")
            login_status = gr.Markdown("")
        
        # TTS Interface
        with gr.Column(visible=not access_enabled) as tts_interface:
            gr.Markdown("""
            # 🦜 VieNeu-TTS
            
            Vietnamese Text-to-Speech with Voice Cloning
            """)
            
            # Model Status
            model_status = gr.Markdown(get_model_status_text())
            refresh_status_btn = gr.Button("🔄 Refresh Status", size="sm")
            
            with gr.Row():
                # Input Column
                with gr.Column(scale=3):
                    text_input = gr.Textbox(
                        label="Text to Synthesize",
                        lines=6,
                        placeholder="Enter Vietnamese text here...",
                        value="Xin chào! Đây là hệ thống tổng hợp giọng nói tiếng Việt với khả năng nhân bản giọng nói."
                    )
                    
                    with gr.Tabs() as tabs:
                        with gr.TabItem("👤 Preset Voices", id="preset_mode"):
                            available_voices = get_available_voices()
                            voice_select = gr.Dropdown(
                                choices=available_voices,
                                value=available_voices[0] if available_voices else None,
                                label="Select Voice"
                            )
                        
                        with gr.TabItem("🎙️ Custom Voice", id="custom_mode"):
                            custom_audio = gr.Audio(label="Reference Audio (.wav)", type="filepath")
                            custom_text = gr.Textbox(label="Reference Text", placeholder="Transcript of reference audio")
                    
                    use_batch = gr.Checkbox(
                        value=True,
                        label="⚡ Batch Processing (faster when available)",
                    )
                    
                    current_mode = gr.Textbox(visible=False, value="preset_mode")
                    
                    synthesize_btn = gr.Button("🎵 Synthesize", variant="primary", size="lg")
                
                # Output Column
                with gr.Column(scale=2):
                    audio_output = gr.Audio(
                        label="Generated Audio",
                        type="filepath",
                        autoplay=True
                    )
                    status_output = gr.Textbox(label="Status", interactive=False)
        
        # JavaScript to store token in localStorage
        store_token_js = """
        function(login_visible, tts_visible, token, status) {
            if (token) {
                localStorage.setItem('vieneu_user_session', token);
                console.log('User token stored in localStorage');
            }
            return [login_visible, tts_visible, token, status];
        }
        """
        
        # Event handlers
        if access_enabled:
            login_btn.click(
                fn=user_login,
                inputs=[username_input, password_input],
                outputs=[login_page, tts_interface, session_token, login_status],
                js=store_token_js
            )
        
        # Load event to restore session
        user_interface.load(
            fn=validate_and_restore_user_session,
            inputs=[session_token],
            outputs=[
                login_page,
                tts_interface,
                session_token,
                login_status,
                model_status,
                voice_select
            ]
        )
        
        tabs.children[0].select(lambda: "preset_mode", outputs=current_mode)
        tabs.children[1].select(lambda: "custom_mode", outputs=current_mode)
        
        def refresh_status_and_voices(current_voice):
            """Refresh model status and update voice dropdown."""
            status_text = get_model_status_text()
            available_voices = get_available_voices()
            
            # If current voice is still in list, keep it; otherwise use first available
            new_value = current_voice if current_voice in available_voices else (available_voices[0] if available_voices else None)
            
            return status_text, gr.update(choices=available_voices, value=new_value)
        
        refresh_status_btn.click(
            fn=refresh_status_and_voices,
            inputs=[voice_select],
            outputs=[model_status, voice_select]
        )
        
        synthesize_btn.click(
            fn=synthesize_tts,
            inputs=[session_token, text_input, voice_select, custom_audio, custom_text, current_mode, use_batch],
            outputs=[audio_output, status_output]
        )
    
    return user_interface
