# Design: Session Persistence and Admin Dashboard Fixes

## Context
The current Gradio-based admin and user interfaces use `gr.State()` for session tokens. This state is lost on page reload because it only exists in the browser's JavaScript runtime during a single page session. The server-side SessionManager works correctly, but tokens are not persisted client-side.

## Goals
- Sessions should persist across browser refreshes (until expiry or logout)
- Model status should reflect server state on every page load
- Access protection toggle should work reliably
- Admins should have a clear user list with inline management actions

## Non-Goals
- Implementing traditional cookie-based sessions (Gradio's architecture makes this complex)
- Multi-tab session synchronization
- "Remember me" functionality beyond the 24-hour session timeout

## Decisions

### Decision 1: Use localStorage for Token Persistence
**What**: Store session tokens in browser localStorage, restore on page load
**Why**: 
- Gradio's `gr.State()` doesn't persist across page reloads
- localStorage is simple and works within Gradio's JavaScript execution model
- Avoids complex cookie handling with Gradio's internal HTTP handling

**Implementation approach**:
```python
# Add JavaScript to store token after login
js_store_token = """
function(token) {
    if (token) localStorage.setItem('vieneu_session', token);
    return token;
}
"""

# Add JavaScript to recover token on page load
js_recover_token = """
function() {
    return localStorage.getItem('vieneu_session') || '';
}
"""
```

### Decision 2: Page Load Session Recovery
**What**: On page load, check localStorage for existing token, validate with server, and restore authenticated state if valid
**Why**: Provides seamless experience without re-authentication after refresh

**Implementation approach**:
```python
# Add load event handler
admin_interface.load(
    fn=recover_session,
    inputs=[],
    outputs=[login_page, dashboard_page, session_token, model_status_display, ...]
)
```

### Decision 3: Enhanced User List with DataFrame
**What**: Replace markdown-based user list with Gradio DataFrame component for better UX
**Why**: 
- Supports inline actions (enable/disable, remove)
- Better visual presentation for larger user sets
- Native sorting/filtering capabilities

**Alternative considered**: Keep markdown but add separate action buttons per user - rejected as too clunky with many users

## Risks / Trade-offs

### Risk: localStorage Security
- **Risk**: Token stored in localStorage accessible to XSS attacks
- **Mitigation**: 
  - 24-hour token expiry limits exposure window
  - Server validates all requests regardless of token
  - Admin actions require re-validation

### Risk: Gradio JavaScript Execution Timing
- **Risk**: JavaScript may not execute in expected order on page load
- **Mitigation**: Use Gradio's `.load()` event which fires after interface is ready

## Migration Plan
No migration needed - this is a bug fix and enhancement to existing functionality.

## Open Questions
1. Should we implement CSRF protection for admin actions?
2. Should tokens be stored with expiry timestamp in localStorage for client-side expiry check?
