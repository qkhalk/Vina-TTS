# Change: Filter Voice Selection Based on Model Configuration

## Why
When using quantized GGUF backbone models (e.g., VieNeu-TTS-q4-gguf or VieNeu-TTS-q8-gguf), only 4 voices are recommended/supported, but the client UI shows all 9 voices. This leads to errors or poor performance when users select unsupported voices.

The previous implementation (`gradio_app.py.bak`) had a `GGUF_ALLOWED_VOICES` list that filtered voices based on the backbone model type, but this logic was removed during the admin/user interface refactoring.

## What Changes
- Add voice filtering logic to `model_manager.py` that determines supported voices based on loaded model configuration
- Modify `gradio_user.py` to dynamically filter voice dropdown choices based on the currently loaded model
- Update voice selection to only show voices compatible with the current backbone + codec combination
- Add API endpoint to retrieve supported voices from ModelManager

**Key Rules:**
- GGUF backbone models (any codec) → Show only 4 optimized voices (Vĩnh, Bình, Ngọc, Dung)
- Non-GGUF backbone models → Show all 9 voices
- Codec type does not affect voice filtering
- Custom voice mode always available (user provides their own reference)

## Impact
- **Affected specs**: `voice-selection` (new capability)
- **Affected code**: 
  - `model_manager.py` (add `get_supported_voices()` method)
  - `gradio_user.py` (add voice filtering on page load and model status refresh)
  - `config.yaml` (document voice compatibility metadata)
- **User experience**: Users will only see voices that work with their loaded model configuration, preventing errors
- **Breaking changes**: None (enhancement only)
