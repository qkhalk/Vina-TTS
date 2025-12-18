## 1. Authentication Module

- [ ] 1.1 Create `auth/` directory structure
- [ ] 1.2 Implement `auth/models.py` - User dataclass and types
- [ ] 1.3 Implement `auth/admin_auth.py` - Admin password verification from env
- [ ] 1.4 Implement `auth/user_auth.py` - User CRUD operations with JSON file
- [ ] 1.5 Implement `auth/session.py` - Session management utilities
- [ ] 1.6 Add bcrypt to dependencies in `pyproject.toml`
- [ ] 1.7 Create `config/users.json.example` template
- [ ] 1.8 Add `config/users.json` to `.gitignore`

## 2. Model Manager

- [ ] 2.1 Create `model_manager.py` - Singleton pattern for TTS model
- [ ] 2.2 Implement load/unload/restart methods with thread safety
- [ ] 2.3 Add health status tracking (loaded, loading, error, unloaded)
- [ ] 2.4 Migrate model loading logic from `gradio_app.py`
- [ ] 2.5 Add memory cleanup on unload

## 3. Admin Interface

- [ ] 3.1 Create `gradio_admin.py` with admin-only components
- [ ] 3.2 Implement admin login page
- [ ] 3.3 Add model control panel (load/unload/restart buttons)
- [ ] 3.4 Add model configuration (backbone, codec, device selection)
- [ ] 3.5 Add user management panel (list, add, remove, enable/disable users)
- [ ] 3.6 Add toggle for user access protection (enable/disable password requirement)
- [ ] 3.7 Display model status and system metrics (GPU memory, etc.)

## 4. User Interface

- [ ] 4.1 Create `gradio_user.py` with user-facing components
- [ ] 4.2 Implement conditional login page (when access protection enabled)
- [ ] 4.3 Port TTS synthesis UI from existing `gradio_app.py`
- [ ] 4.4 Remove configuration options (backbone, codec, device)
- [ ] 4.5 Add model status indicator (ready/unavailable)
- [ ] 4.6 Handle graceful degradation when model not loaded

## 5. Main Application

- [ ] 5.1 Update `gradio_app.py` to mount admin and user interfaces
- [ ] 5.2 Configure routing (`/admin` for admin, `/` for user)
- [ ] 5.3 Add auth middleware for route protection
- [ ] 5.4 Update environment variable handling (add ADMIN_PASSWORD, SECRET_KEY)
- [ ] 5.5 Update `.env.example` with new variables

## 6. Configuration & Documentation

- [ ] 6.1 Update `config.yaml` if needed for new settings
- [ ] 6.2 Update Docker configuration for new env vars
- [ ] 6.3 Add admin/user setup instructions to README (brief)

## 7. Testing & Validation

- [ ] 7.1 Test admin login flow
- [ ] 7.2 Test user login flow (when enabled)
- [ ] 7.3 Test model load/unload/restart from admin
- [ ] 7.4 Test user synthesis when model loaded
- [ ] 7.5 Test graceful handling when model not loaded
- [ ] 7.6 Test concurrent access (multiple users)
- [ ] 7.7 Verify no resource leaks on model reload
