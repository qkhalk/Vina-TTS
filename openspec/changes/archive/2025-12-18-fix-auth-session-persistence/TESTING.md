# Testing Guide

## Prerequisites
1. Start the application with both admin and user interfaces
2. Ensure you have admin password set in environment variable
3. Have at least one test user created

## Test Cases

### 1. Admin Login Persistence

**Steps:**
1. Navigate to admin interface
2. Login with admin password
3. Verify dashboard is displayed
4. Open browser console and check for "Admin token stored in localStorage" message
5. Refresh the page (F5 or Ctrl+R)
6. Verify you remain logged in (dashboard still visible, no login prompt)
7. Check browser console for "Recovering admin session: Token found" message

**Expected Result:** Admin stays logged in after page refresh

### 2. User Login Persistence (with Access Protection Enabled)

**Steps:**
1. In admin dashboard, enable "User Access Protection"
2. Navigate to user interface
3. Login with test user credentials
4. Verify TTS interface is displayed
5. Open browser console and check for "User token stored in localStorage" message
6. Refresh the page
7. Verify you remain logged in (TTS interface still visible)
8. Check browser console for "Recovering user session: Token found" message

**Expected Result:** User stays logged in after page refresh

### 3. User Interface with Access Protection Disabled

**Steps:**
1. In admin dashboard, disable "User Access Protection"
2. Navigate to user interface
3. Verify TTS interface is directly accessible without login
4. Refresh the page
5. Verify TTS interface remains accessible

**Expected Result:** No login required when protection is disabled

### 4. Model Status Persistence

**Steps:**
1. Login to admin dashboard
2. Load a model (select backbone, codec, device)
3. Wait for model to load successfully
4. Note the model status display
5. Refresh the page
6. Verify dashboard restores and shows correct model status
7. Click "Refresh Status" button to confirm status is accurate

**Expected Result:** Model status persists across page refresh

### 5. Access Protection Toggle

**Steps:**
1. Login to admin dashboard
2. Enable "User Access Protection" checkbox
3. Verify success message appears
4. Refresh the page
5. Verify checkbox is still checked
6. Uncheck the "User Access Protection" checkbox
7. Verify success message appears
8. Refresh the page
9. Verify checkbox is still unchecked

**Expected Result:** Toggle state persists correctly in both directions

### 6. User List Display

**Steps:**
1. Login to admin dashboard
2. Navigate to "User Management" section
3. Verify user list displays in table format with columns:
   - Username
   - Status (✅ Enabled / ❌ Disabled)
   - Created Date
   - Actions placeholder

**Expected Result:** Clean table display with user information

### 7. Add User

**Steps:**
1. In admin dashboard, go to "Add New User" section
2. Enter username and password (min 8 chars)
3. Click "Add User" button
4. Verify success message
5. Check that new user appears in user list table
6. Check that new user appears in "Select User" dropdown

**Expected Result:** User is added and appears in both list and dropdown

### 8. Enable/Disable User

**Steps:**
1. In admin dashboard, select a user from the dropdown
2. Click "Disable User" button
3. Verify success message appears
4. Check user list shows "❌ Disabled" for that user
5. Click "Enable User" button
6. Verify success message appears
7. Check user list shows "✅ Enabled" for that user

**Expected Result:** User status changes correctly

### 9. Remove User

**Steps:**
1. In admin dashboard, select a user from the dropdown
2. Click "Remove User" button
3. Verify success message appears
4. Check that user disappears from user list table
5. Check that user disappears from dropdown
6. Verify dropdown clears selection

**Expected Result:** User is removed from all displays

### 10. Session Expiry

**Steps:**
1. Login to admin or user interface
2. Wait for 24 hours (or modify session timeout in code for faster testing)
3. Try to perform an action (load model, synthesize, etc.)
4. Verify you are logged out and redirected to login page

**Expected Result:** Sessions expire after 24 hours

### 11. Cross-Tab Behavior

**Steps:**
1. Open admin interface in one tab
2. Login
3. Open admin interface in another tab
4. Verify both tabs show dashboard (session shared via localStorage)
5. Logout is not implemented yet, so manual clearing:
   - Open browser console
   - Run: `localStorage.removeItem('vieneu_admin_session')`
   - Refresh both tabs
6. Verify both tabs show login page

**Expected Result:** Session persists across tabs

### 12. Invalid/Expired Token Handling

**Steps:**
1. Login to admin interface
2. Open browser console
3. Corrupt the token: `localStorage.setItem('vieneu_admin_session', 'invalid_token')`
4. Refresh the page
5. Verify you are shown login page (invalid token handled gracefully)
6. Check console for "Recovering admin session: Token found" followed by redirect to login

**Expected Result:** Invalid tokens are handled gracefully with redirect to login

## Cleanup After Testing

To clear all sessions and start fresh:
```javascript
// In browser console
localStorage.removeItem('vieneu_admin_session');
localStorage.removeItem('vieneu_user_session');
```

## Known Limitations

1. **No explicit logout button**: Users need to manually clear localStorage or wait for 24h expiry
2. **No "Remember Me" option**: All sessions are 24 hours by default
3. **No CSRF protection**: Admin actions should ideally have CSRF tokens
4. **localStorage security**: Tokens are accessible to XSS attacks (mitigated by 24h expiry)
