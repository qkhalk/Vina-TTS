## Context
VieNeu-TTS inference requires GPU resources (T4-level for PyTorch, or CPU for GGUF Q4). Administrators need flexibility to choose between local and remote (Colab) backends depending on their current situation:
- Local machine has GPU → use local for lower latency
- Local machine is resource-limited → use Colab's free T4 GPU
- Testing/development → switch between backends easily

**Stakeholders**: Administrators managing VieNeu-TTS deployments, end users consuming TTS API.

**Constraints**:
- Colab free tier: 12hr runtime, may disconnect if idle
- Network latency: ~100-500ms round-trip to Colab
- Security: Public tunnel URLs need authentication
- Model download: 3-5GB from HuggingFace on each Colab restart

## Goals / Non-Goals

**Goals**:
- Admin can freely choose between Local and Colab backend modes
- Admin can switch backend modes without restarting the application
- Admin can have local model loaded while also having Colab connected (ready to switch)
- TTS requests transparently route to selected backend
- System monitors both backends and reports status in admin UI
- Pre-built notebook eliminates manual dependency installation
- Clear documentation for users on how to set up and use Colab integration

**Non-Goals**:
- Auto-provisioning Colab runtimes (requires Google account interaction)
- Persistent Colab sessions beyond 12hr limit
- Load balancing across multiple Colab instances
- Simultaneous use of both backends for same request
- Kaggle integration (similar pattern, future work)

## Decisions

### 1. Communication Protocol: HTTP REST API
**Decision**: Colab runs a FastAPI server exposing `/tts/synthesize` endpoint, admin connects via tunnel URL.

**Alternatives considered**:
- WebSocket streaming: Higher complexity, latency benefit minimal for TTS (batch response)
- gRPC: Overkill for single-endpoint use case, harder to debug
- Gradio share: Would expose full UI, not just API; harder to integrate

**Rationale**: REST is simple, debuggable, and compatible with existing inference flow.

### 2. Tunnel Solution: ngrok (primary), cloudflared (alternative)
**Decision**: Notebook includes `pyngrok` for auto-tunnel, with manual cloudflared instructions as fallback.

**Rationale**: ngrok is well-documented, stable, and works in Colab. cloudflared is free but requires manual setup.

### 3. Authentication: Shared Secret Token
**Decision**: Generate random token in notebook, paste into admin UI. All API requests include `Authorization: Bearer <token>` header.

**Alternatives considered**:
- OAuth: Overkill for single-admin use case
- IP whitelisting: Colab IPs dynamic, admin IPs often change
- No auth: Exposes public TTS endpoint (abuse risk)

**Rationale**: Simple, secure enough for intended use case.

### 4. Backend Mode Switching in ModelManager
**Decision**: Add `backend_mode` enum to ModelManager: `LOCAL`, `REMOTE`. 
- Local model and Colab connection are managed independently
- `backend_mode` determines which one is used for TTS requests
- Admin can have both ready and switch instantly

**Rationale**: 
- Maximum flexibility for admin to choose based on current needs
- No restart required to switch backends
- Local model stays loaded even when using Colab (and vice versa)

### 5. Notebook Generation: Jinja2 Template
**Decision**: Store notebook template as `.ipynb.j2` file, render with admin-configured values (model, voice samples, auth token).

**Rationale**: Allows customization without editing raw JSON; admin can regenerate with different settings.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     VPS / Local Server                          │
│                                                                 │
│  ┌─────────────┐    ┌──────────────────────────────────────┐   │
│  │ Gradio User │───▶│         Model Manager                │   │
│  │     UI      │    │  ┌────────────────────────────────┐  │   │
│  └─────────────┘    │  │     backend_mode: LOCAL/REMOTE │  │   │
│                     │  └────────────────────────────────┘  │   │
│                     │           │                │         │   │
│                     │           ▼                ▼         │   │
│                     │  ┌─────────────┐  ┌───────────────┐  │   │
│                     │  │ Local Model │  │ColabTTSClient │  │   │
│                     │  │ (VieNeuTTS) │  │ (HTTP proxy)  │  │   │
│                     │  └─────────────┘  └───────┬───────┘  │   │
│                     └──────────────────────────────────────┘   │
│                                                   │             │
│  ┌─────────────┐    Backend Selection            │             │
│  │ Gradio Admin│─────────────────────────────────┘             │
│  │     UI      │  • Mode: Local / Colab                        │
│  └─────────────┘  • Colab URL + Token                          │
│                   • Download Notebook                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                    HTTP (ngrok tunnel)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Google Colab Runtime                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐     │
│  │ FastAPI     │───▶│ VieNeuTTS / │───▶│  NeuCodec       │     │
│  │ Server      │    │ FastVieNeuTTS│    │  (T4 GPU)       │     │
│  └─────────────┘    └─────────────┘    └─────────────────┘     │
│        │                                                        │
│        │         ngrok tunnel                                   │
│        └────────────────────────────────────────────────────────│
└─────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- Local model and Colab client are independent - both can be ready simultaneously
- `backend_mode` acts as a switch to route TTS requests
- Admin can switch modes instantly without unloading/reconnecting

## API Design

### Colab API Server Endpoints

```
POST /tts/synthesize
  Headers: Authorization: Bearer <token>
  Body: {
    "text": "Xin chào",
    "voice_sample_path": "samples/vinh.wav",  # or base64 audio
    "voice_transcript": "...",
    "speed": 1.0,
    "watermark": true
  }
  Response: {
    "audio_base64": "...",
    "sample_rate": 24000,
    "duration_ms": 1234
  }

GET /health
  Headers: Authorization: Bearer <token>
  Response: {
    "status": "ok",
    "model_loaded": true,
    "gpu_memory_used_gb": 4.2,
    "uptime_seconds": 3600
  }
```

### Admin UI Configuration

```yaml
# config.yaml additions
colab:
  enabled: false
  endpoint_url: ""  # e.g., "https://abc123.ngrok.io"
  auth_token: ""
  timeout_seconds: 60
  health_check_interval: 30
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Colab runtime disconnects unexpectedly | Health check polling; auto-fallback to local mode with user notification |
| 12hr runtime limit | Admin UI shows remaining time estimate; reminder to reconnect |
| Network latency adds 100-500ms | Acceptable for TTS use case; batch requests when possible |
| ngrok rate limits (free tier) | Document limits; provide cloudflared alternative |
| Model download on every restart | Cache on Google Drive (optional setup in notebook) |
| Public tunnel abuse | Auth token required; rate limiting in FastAPI |

## Migration Plan
- **Phase 1**: Add Colab module, notebook template, admin UI panel (no breaking changes)
- **Phase 2**: Integrate with ModelManager remote mode
- **Rollback**: Disable colab.enabled in config, system continues with local mode

## Open Questions
1. Should we support uploading custom voice samples from admin UI to Colab, or require pre-configured voices?
   - **Tentative answer**: Start with pre-configured voices in notebook; add upload in future iteration
2. Should notebook auto-mount Google Drive for model caching?
   - **Tentative answer**: Include as optional cell (commented out by default)
