# Change: Add Google Colab Integration with Hybrid Backend Selection

## Why
VieNeu-TTS requires significant GPU/CPU resources for model inference. Administrators need flexibility to choose between:
- **Local mode**: Run model on local machine (when GPU available or for low latency)
- **Remote mode**: Offload to Google Colab (when local resources limited or for free T4 GPU)

This hybrid approach allows dynamic switching based on current needs - not always using Colab, not always using local machine.

## What Changes
- **ADDED**: Colab Backend Manager - Module to manage Colab runtime connections (ngrok/cloudflare tunnel URLs)
- **ADDED**: Admin UI - "Backend Selection" panel in admin dashboard for:
  - **Backend Mode selector**: Choose between "Local" or "Google Colab"
  - Generating pre-configured Colab notebook (one-click download)
  - Configuring remote Colab endpoint URL and auth token
  - Testing connection and health status
  - Visual status indicators for both backends
- **ADDED**: Remote TTS Client - HTTP client to proxy TTS requests to Colab runtime
- **ADDED**: Colab Notebook Template - Pre-built notebook with auto-setup (espeak-ng, dependencies, model loading, API server)
- **ADDED**: User Instructions - `docs/colab-integration.md` with setup guide
- **MODIFIED**: Model Manager - Support for `backend_mode` (LOCAL/REMOTE) with seamless switching
- **MODIFIED**: Admin Dashboard - Reorganized model control to show current backend mode clearly
- **MODIFIED**: TTS inference flow - Route requests through selected backend

## Impact
- **Affected specs**: `admin-auth` (new admin UI panel), new `colab-integration` capability
- **Affected code**:
  - `gradio_admin.py` - Backend selection panel with mode toggle
  - `model_manager.py` - Backend mode enum and switching logic
  - New `colab/` module - Notebook template, client, backend manager
  - `config.yaml` - Backend mode and Colab endpoint configuration
  - New `docs/colab-integration.md` - User instructions
- **Security**: Remote endpoint requires authentication token exchange
- **Breaking changes**: None - additive feature, existing local mode unchanged

## Success Criteria
1. Admin can select backend mode: "Local" or "Google Colab"
2. Admin can load/unload local model independently of Colab connection
3. Admin can download pre-configured Colab notebook from admin UI
4. Admin can connect to Colab and switch to remote mode seamlessly
5. TTS requests route to selected backend transparently
6. Clear status display showing which backend is active
7. Instructions document created at `docs/colab-integration.md`
