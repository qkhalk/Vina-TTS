# Change: Fix Authentication Session Persistence and Admin Dashboard Issues

## Why
The current authentication system has several bugs and missing features that impact usability:
1. Sessions are lost on page reload, requiring users/admins to re-enter credentials
2. Model status does not persist in the UI after page refresh despite server-side singleton
3. User Access Protection toggle cannot be disabled once enabled (due to lost session)
4. No comprehensive user list management feature for admins

## What Changes
- **Session Persistence**: Implement browser-side session token storage (localStorage/cookies) so sessions survive page reloads
- **Model Status Sync**: Ensure admin dashboard loads correct model status on page load/refresh
- **Access Protection Fix**: Fix the toggle to work properly with session persistence
- **User List Feature**: Add comprehensive user list table with enable/disable and remove actions inline

## Impact
- Affected specs: `admin-auth`
- Affected code:
  - `auth/session.py` - Session token persistence mechanism
  - `gradio_admin.py` - Session recovery on page load, user list UI improvements
  - `gradio_user.py` - Session recovery on page load
