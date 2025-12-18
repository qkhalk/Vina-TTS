## 1. Core Infrastructure

- [x] 1.1 Create `colab/` module directory structure
- [x] 1.2 Implement `colab/client.py` - ColabTTSClient HTTP proxy class
  - [x] POST /tts/synthesize with auth token
  - [x] GET /health endpoint check
  - [x] Connection timeout and retry logic
  - [x] Response parsing (base64 audio decode)
- [x] 1.3 Implement `colab/config.py` - Colab configuration dataclass
- [x] 1.4 Add colab section to `config.yaml` schema

## 2. Notebook Template

- [x] 2.1 Create `colab/notebook_template.ipynb` - Base Colab notebook
  - [x] Cell 1: Mount Google Drive (optional, commented)
  - [x] Cell 2: Install system dependencies (espeak-ng)
  - [x] Cell 3: Install Python dependencies (uv or pip)
  - [x] Cell 4: Download model from HuggingFace
  - [x] Cell 5: Start FastAPI server with ngrok tunnel
  - [x] Cell 6: Display connection URL and auth token
- [x] 2.2 Implement `colab/notebook_generator.py` - Jinja2 template renderer
  - [x] Accept model config (backbone, codec, device)
  - [x] Generate unique auth token
  - [x] Render and return .ipynb file content

## 3. FastAPI Server (runs in Colab)

- [x] 3.1 FastAPI TTS server code embedded in notebook_template.ipynb
  - [x] POST /tts/synthesize endpoint
  - [x] GET /health endpoint
  - [x] Bearer token auth middleware
  - [x] Error handling with proper HTTP codes
- [x] 3.2 Add pyngrok integration for auto-tunnel
- [x] 3.3 Add startup banner with connection info

## 4. ModelManager Integration

- [x] 4.1 Add `BackendMode` enum to model_manager.py (LOCAL, REMOTE)
- [x] 4.2 Add `backend_mode` property with getter/setter
- [x] 4.3 Add `colab_client` property to hold ColabTTSClient instance
- [x] 4.4 Add `set_colab_connection()` method to configure Colab endpoint
- [x] 4.5 Add `disconnect_colab()` method
- [x] 4.6 Modify `get_model()` to return appropriate backend based on mode
- [x] 4.7 Add `get_active_backend_status()` method for UI display
- [x] 4.8 Keep local model and Colab client independent (both can be ready)

## 5. Admin UI Panel

- [x] 5.1 Add "Backend Selection" collapsible group in gradio_admin.py
- [x] 5.2 Add Backend Mode selector (Radio: "Local" / "Google Colab")
- [x] 5.3 Add Local Backend status display (model loaded, GPU memory)
- [x] 5.4 Add Colab Backend controls:
  - [x] Endpoint URL textbox
  - [x] Auth token textbox (password type)
  - [x] "Connect" / "Disconnect" buttons
  - [x] "Test Connection" button
  - [x] "Download Notebook" button
  - [x] Connection status display (connected, latency, GPU memory)
- [x] 5.5 Add visual indicator showing active backend mode
- [x] 5.6 Implement `switch_backend_mode_action()` - switches between LOCAL/REMOTE
- [x] 5.7 Implement `generate_notebook_action()` - triggers notebook download
- [x] 5.8 Implement `connect_colab_action()` - validates and saves endpoint
- [x] 5.9 Implement `disconnect_colab_action()` - clears Colab connection
- [x] 5.10 Implement `test_colab_connection_action()` - calls health endpoint
- [x] 5.11 Periodic health check can be added via Gradio's `gr.Timer()` (optional enhancement)

## 6. Configuration Persistence

- [x] 6.1 Add colab config loading in app startup (via colab/config_loader.py)
- [x] 6.2 Implement save/load of colab endpoint to config.yaml
- [x] 6.3 Add environment variable overrides (COLAB_ENDPOINT_URL, COLAB_AUTH_TOKEN)

## 7. Testing

- [ ] 7.1 Manual test: Generate notebook, run in Colab, connect from admin
- [ ] 7.2 Manual test: TTS synthesis through Colab backend
- [ ] 7.3 Manual test: Switch between Local and Colab modes
- [ ] 7.4 Manual test: Both backends ready, instant switching
- [ ] 7.5 Manual test: Colab disconnect handling

## 8. Documentation

- [x] 8.1 Create `docs/colab-integration.md` with:
  - [x] Overview and use cases
  - [x] Prerequisites (Google account, ngrok account optional)
  - [x] Step-by-step setup guide with screenshots placeholders
  - [x] Troubleshooting common issues
  - [x] FAQ section
- [x] 8.2 Add inline help text in admin UI (via gr.Markdown instructions)
- [x] 8.3 Add tooltips for Colab configuration fields (via `info` parameter)

## 9. Error Handling & UX

- [x] 9.1 Add clear error messages for common failures (timeout, auth, model not loaded)
- [x] 9.2 Loading spinners handled by Gradio default behavior during async operations
- [x] 9.3 Add visual badge showing current active backend (🟢/🔴/⚪ status indicators)
- [ ] 9.4 Add Colab runtime timer estimate display (optional - future enhancement)
