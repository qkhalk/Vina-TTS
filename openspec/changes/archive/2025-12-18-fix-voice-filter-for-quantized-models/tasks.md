# Implementation Tasks

## 1. Backend Changes

- [x] 1.1 Add voice compatibility constants to `model_manager.py`
  - Define `GGUF_OPTIMIZED_VOICES` list with the 4 voices that have pre-encoded codes
  - Add comments explaining the optimization rationale

- [x] 1.2 Implement `get_supported_voices()` method in ModelManager
  - Check current backbone model repository name
  - Apply filtering rules: if "gguf" in backbone repo name → limited voices (4), else → all voices (9)
  - Codec type does NOT affect voice filtering
  - Return filtered list of voice names
  - Handle case when no model is loaded (return all voices)

- [x] 1.3 Update `get_status()` to include supported voices
  - Add `supported_voices` field to status dict
  - Call `get_supported_voices()` to populate this field

## 2. Frontend Changes

- [x] 2.1 Update `gradio_user.py` to use filtered voices
  - Replace static `VOICE_SAMPLES.keys()` with dynamic voice list
  - Create `get_available_voices()` helper that calls `model_manager.get_supported_voices()`
  - Filter `VOICE_SAMPLES` to only include supported voices

- [x] 2.2 Add voice dropdown update on model status refresh
  - When user clicks "Refresh Status", update voice dropdown choices
  - If currently selected voice is not in new list, reset to first available voice
  - Preserve selection if voice is still available

- [x] 2.3 Update interface initialization
  - On page load, get supported voices from model manager
  - Initialize voice dropdown with filtered list
  - Ensure fallback to all voices if model status unavailable

## 3. Testing & Validation

- [x] 3.1 Manual test: GGUF model with ONNX codec
  - Load VieNeu-TTS-q4-gguf with NeuCodec ONNX (Fast CPU)
  - Verify client shows only 4 voices: Vĩnh, Bình, Ngọc, Dung
  - Test synthesis with each filtered voice
  - Verify unsupported voices are hidden

- [x] 3.2 Manual test: GGUF model with Standard codec
  - Load VieNeu-TTS-q8-gguf with NeuCodec (Standard)
  - Verify client STILL shows only 4 voices (codec doesn't matter)
  - Test synthesis works correctly

- [x] 3.3 Manual test: Non-GGUF model with any codec
  - Load VieNeu-TTS (GPU) with NeuCodec ONNX or Standard
  - Verify client shows all 9 voices
  - Test synthesis with various voices

- [x] 3.4 Manual test: Dynamic updates
  - Start with GGUF + ONNX (4 voices shown)
  - Admin switches to non-GGUF model
  - User clicks "Refresh Status"
  - Verify dropdown now shows all 9 voices

- [x] 3.5 Manual test: Custom voice mode
  - Verify custom voice tab is always available
  - Test custom voice synthesis works regardless of model config

## 4. Documentation

- [x] 4.1 Update code comments
  - Document voice filtering logic in model_manager.py
  - Add comments explaining GGUF optimization rationale

- [x] 4.2 Update IMPLEMENTATION_SUMMARY.md if needed
  - Document the voice filtering feature
  - Explain model-specific voice compatibility
  - Note: This can be done after user confirms the feature works as expected
