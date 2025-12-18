# Project Context

## Purpose
VieNeu-TTS is an advanced on-device Vietnamese Text-to-Speech (TTS) system with instant voice cloning capabilities. Trained on ~1000 hours of high-quality Vietnamese speech, it supports:
- Production-ready Vietnamese speech synthesis (offline)
- Code-switching between Vietnamese and English
- Real-time 24kHz waveform generation on CPU or GPU
- Multiple model formats: PyTorch, GGUF Q4/Q8, ONNX

## Tech Stack
- **Language**: Python 3.12+
- **Package Manager**: uv (with `uv sync` for dependencies)
- **Deep Learning**: PyTorch, Transformers (Qwen 0.5B backbone)
- **Audio Codec**: NeuCodec (torch, ONNX variants)
- **Quantization**: llama-cpp-python for GGUF models
- **GPU Optimization**: LMDeploy TurbomindEngine, Triton compilation
- **Web UI**: Gradio
- **Audio Processing**: librosa, soundfile
- **Text Processing**: phonemizer (requires eSpeak NG system dependency)
- **Containerization**: Docker, docker-compose

## Project Conventions

### Code Style
- Type hints for function parameters and return types
- Docstrings for public methods (Google style)
- Constants in UPPER_SNAKE_CASE at module level
- Classes use PascalCase, functions/variables use snake_case
- Private methods prefixed with underscore (e.g., `_load_backbone`)
- Match statements for codec/model dispatch
- Minimal inline comments; code should be self-documenting

### Architecture Patterns
- **Core TTS Classes**: `VieNeuTTS` (standard CPU/GPU), `FastVieNeuTTS` (LMDeploy optimized)
- **Utilities**: Separate modules for text normalization, phonemization, and chunking
- **Configuration**: YAML-based config (`config.yaml`) for models, codecs, voice samples
- **Reference Caching**: Pre-encoded `.pt` files for voice samples (ONNX codec optimization)
- **Streaming**: Generator-based streaming with overlap-add for smooth audio

### Testing Strategy
- Manual testing via Gradio UI and example scripts
- No automated test suite currently defined

### Git Workflow
- Main branch: `main`
- Feature branches: `feature/amazing-feature`
- Commit style: Descriptive messages (e.g., "Add amazing feature")
- PRs welcome with fork -> feature branch -> PR flow

## Domain Context
- **Phonemization**: Vietnamese text converted to phonemes via eSpeak NG + custom dictionary (`phoneme_dict.json`)
- **Text Normalization**: Handles Vietnamese-specific patterns (numbers, abbreviations, etc.)
- **Voice Cloning**: Uses reference audio (3-10s) + transcript to clone voice characteristics
- **Speech Tokens**: Model generates `<|speech_N|>` tokens decoded by NeuCodec to waveform
- **Chunking**: Long text split into ~256 char chunks for context window limits (2048 tokens)

## Important Constraints
- **Context Window**: 2048 tokens shared between prompt text and speech tokens
- **ONNX Codec**: CPU-only, requires pre-encoded `.pt` reference codes
- **eSpeak NG**: Required system dependency for phonemization
- **CUDA**: LMDeploy/FastVieNeuTTS requires NVIDIA GPU with CUDA
- **Audio Watermark**: Enabled by default on generated audio

## External Dependencies
- **Hugging Face Hub**: Model hosting (`pnnbao-ump/VieNeu-TTS`, `neuphonic/neucodec`)
- **eSpeak NG**: System-level TTS engine for phoneme conversion
- **PyTorch Index**: CUDA 11.8 wheels from `download.pytorch.org/whl/cu118`
