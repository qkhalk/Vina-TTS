## 1. Authentication Module

- [x] 1.1 Create `auth/` directory structure
- [x] 1.2 Implement `auth/models.py` - User dataclass and types
- [x] 1.3 Implement `auth/admin_auth.py` - Admin password verification from env
- [x] 1.4 Implement `auth/user_auth.py` - User CRUD operations with JSON file
- [x] 1.5 Implement `auth/session.py` - Session management utilities
- [x] 1.6 Add bcrypt to dependencies in `pyproject.toml`
- [x] 1.7 Create `config/users.json.example` template
- [x] 1.8 Add `config/users.json` to `.gitignore`

## 2. Model Manager

- [x] 2.1 Create `model_manager.py` - Singleton pattern for TTS model
- [x] 2.2 Implement load/unload/restart methods with thread safety
- [x] 2.3 Add health status tracking (loaded, loading, error, unloaded)
- [x] 2.4 Migrate model loading logic from `gradio_app.py`
- [x] 2.5 Add memory cleanup on unload

## 3. Admin Interface

- [x] 3.1 Create `gradio_admin.py` with admin-only components
- [x] 3.2 Implement admin login page
- [x] 3.3 Add model control panel (load/unload/restart buttons)
- [x] 3.4 Add model configuration (backbone, codec, device selection)
- [x] 3.5 Add user management panel (list, add, remove, enable/disable users)
- [x] 3.6 Add toggle for user access protection (enable/disable password requirement)
- [x] 3.7 Display model status and system metrics (GPU memory, etc.)

## 4. User Interface

- [x] 4.1 Create `gradio_user.py` with user-facing components
- [x] 4.2 Implement conditional login page (when access protection enabled)
- [x] 4.3 Port TTS synthesis UI from existing `gradio_app.py`
- [x] 4.4 Remove configuration options (backbone, codec, device)
- [x] 4.5 Add model status indicator (ready/unavailable)
- [x] 4.6 Handle graceful degradation when model not loaded

## 5. Main Application

- [x] 5.1 Update `gradio_app.py` to mount admin and user interfaces
- [x] 5.2 Configure routing (tabs for admin and user interfaces)
- [x] 5.3 Add auth middleware for route protection
- [x] 5.4 Update environment variable handling (add ADMIN_PASSWORD, SECRET_KEY)
- [x] 5.5 Update `.env.example` with new variables

## 6. Configuration & Documentation

- [x] 6.1 Update `config.yaml` if needed for new settings (no changes needed)
- [x] 6.2 Update Docker configuration for new env vars (uses .env file automatically)
- [x] 6.3 Add admin/user setup instructions to README (brief)

## 7. Testing & Validation

- [x] 7.1 Syntax validation - all files compile successfully
- [x] 7.2 Auth module tested - imports and basic functionality work
- [x] 7.3 ModelManager structure validated
- [x] 7.4 Integration testing deferred to runtime (requires full environment)
- [x] 7.5 Code review completed - all patterns follow OpenSpec requirements
- [x] 7.6 Documentation updated with setup instructions
- [x] 7.7 Dependencies added and .gitignore updated
