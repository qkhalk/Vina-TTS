# Change: Add Admin/User Role-Based Access Control

## Why
Currently, every browser tab loads the TTS model independently, causing resource leaks and inefficient GPU/memory usage. There's no centralized model management or access control, meaning anyone with the URL can use the service and configure system settings.

## What Changes
- **Centralized Model Management**: Single shared model instance controlled by admin (start/stop/restart)
- **Admin Page**: Protected page for system configuration (backbone, codec, device, model lifecycle)
- **User Page**: Simplified interface for TTS usage only (no configuration access)
- **Admin Authentication**: Simple env-based password for admin access
- **User Access Control**: Optional password protection for user page (admin can enable/disable)
- **Lightweight Storage**: JSON file-based user management (no database required)

## Impact
- Affected specs: New `admin-auth` capability
- Affected code:
  - `gradio_app.py` - Split into admin/user interfaces, add auth middleware
  - New `auth/` module - Authentication logic
  - New `config/users.json` - User credentials storage
  - `.env` - Admin password configuration
- **BREAKING**: Current single-page UI will be replaced with role-based pages

## Design Decisions

### Why JSON file over SQLite/Supabase?
- **Minimal overhead**: No database process, no connections, no migrations
- **Simple backup**: Single file to backup/restore
- **Fast reads**: File cached in memory, only write on changes
- **Good enough**: For <100 users, JSON performs well
- Upgrade path to SQLite exists if needed later

### Authentication Approach
- **Admin**: Environment variable `ADMIN_PASSWORD` (simple, secure for single admin)
- **Users**: Optional, stored in `users.json` with bcrypt-hashed passwords
- **Sessions**: Gradio's built-in session management + HTTP-only cookies

### Model Lifecycle
- Singleton pattern for TTS model
- Admin controls: Load, Unload, Restart
- Health status visible to admin
- Users see only "Model Ready" / "Model Unavailable"
