## Context
VieNeu-TTS currently runs as a single Gradio app where every user has full access to model configuration. This causes:
1. Resource leaks when multiple tabs load models independently
2. No access control for production deployments
3. No way to restrict who can use the TTS service

Stakeholders: Server admins, end users, API consumers (future)

## Goals / Non-Goals

### Goals
- Centralized model management (single instance, admin-controlled)
- Role separation (admin configures, user consumes)
- Lightweight auth (no external database dependencies)
- Easy deployment (env vars + single JSON file)

### Non-Goals
- Multi-tenant isolation (single deployment, shared model)
- OAuth/SSO integration (out of scope, can add later)
- API key management (future enhancement)
- User registration flow (admin creates users manually)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Gradio Application                    │
├──────────────────────┬──────────────────────────────────┤
│     Admin Page       │          User Page               │
│  (/admin?token=xxx)  │     (/user or / )                │
├──────────────────────┴──────────────────────────────────┤
│                   Auth Middleware                        │
│         (session validation, role checking)              │
├─────────────────────────────────────────────────────────┤
│                  Model Manager (Singleton)               │
│         (load/unload/restart, health status)             │
├─────────────────────────────────────────────────────────┤
│     Auth Module          │      Config Module            │
│  - admin_auth.py         │   - users.json               │
│  - user_auth.py          │   - .env (ADMIN_PASSWORD)    │
└─────────────────────────────────────────────────────────┘
```

## Decisions

### Decision 1: JSON file for user storage
**Choice**: JSON file (`config/users.json`)
**Why**: Simplest solution that meets requirements
**Alternatives considered**:
- SQLite: Overkill for <100 users, adds complexity
- Supabase: External dependency, network latency, cost
- Environment variables only: Can't dynamically add users

**Trade-off**: Manual file editing for user management (acceptable for small scale)

### Decision 2: Separate Gradio Blocks for Admin/User
**Choice**: Two separate `gr.Blocks()` instances mounted on different routes
**Why**: Clean separation, different layouts, independent auth
**Alternatives considered**:
- Single app with conditional rendering: Complex state management
- Tabs with permission checks: Harder to secure, UI clutter

### Decision 3: Session-based authentication
**Choice**: Server-side sessions with secure cookies
**Why**: Works with Gradio, no client-side token storage issues
**Alternatives considered**:
- JWT tokens: Overkill, harder to invalidate
- Basic auth: Poor UX, browser caches credentials

### Decision 4: Singleton Model Manager
**Choice**: Global `ModelManager` class with thread-safe operations
**Why**: Prevents multiple model loads, centralizes lifecycle
**Implementation**:
```python
class ModelManager:
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
```

## Data Structures

### users.json
```json
{
  "access_enabled": true,
  "users": [
    {
      "username": "user1",
      "password_hash": "$2b$12$...",
      "created_at": "2025-01-01T00:00:00Z",
      "enabled": true
    }
  ]
}
```

### Environment Variables
```bash
ADMIN_PASSWORD=your-secure-password  # Required
USER_ACCESS_ENABLED=true             # Optional, default true
SECRET_KEY=random-32-char-string     # For session signing
```

## File Structure
```
vieneu_tts/
├── auth/
│   ├── __init__.py
│   ├── admin_auth.py      # Admin password verification
│   ├── user_auth.py       # User login/session management
│   ├── session.py         # Session handling utilities
│   └── models.py          # User dataclass
├── config/
│   └── users.json         # User credentials (gitignored)
├── model_manager.py       # Singleton TTS model manager
├── gradio_admin.py        # Admin interface
├── gradio_user.py         # User interface  
└── gradio_app.py          # Main app (mounts both)
```

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| JSON file corruption | Users locked out | Backup on every write, validation on read |
| Forgot admin password | Can't access admin | Document recovery via env var reset |
| Session hijacking | Unauthorized access | Secure cookies, HTTPS in production |
| Concurrent JSON writes | Data loss | File locking with `fcntl`/`msvcrt` |

## Migration Plan

1. **Phase 1**: Add auth module and model manager (non-breaking)
2. **Phase 2**: Create admin/user pages alongside existing app
3. **Phase 3**: Update `gradio_app.py` to use new structure
4. **Phase 4**: Remove old single-page code
5. **Rollback**: Revert to previous `gradio_app.py` if issues

## Security Considerations

- Admin password: Minimum 12 characters enforced
- User passwords: bcrypt with cost factor 12
- Sessions: 24-hour expiry, regenerate on login
- CSRF: Gradio handles internally
- Rate limiting: Consider adding for login endpoints

## Open Questions

1. Should we add rate limiting for failed login attempts?
2. Do we need audit logging for admin actions?
3. Should model status be exposed via a health endpoint for monitoring?
