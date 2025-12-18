# admin-auth Delta Changes

## MODIFIED Requirements

### Requirement: Session Management
The system SHALL manage user and admin sessions securely using server-side storage with client-side token persistence.

#### Scenario: Session creation
- **WHEN** user or admin authenticates successfully
- **THEN** system creates server-side session
- **AND** returns session token to client
- **AND** client stores token in localStorage

#### Scenario: Session recovery on page load
- **WHEN** page loads or refreshes
- **AND** localStorage contains session token
- **THEN** system validates token with server
- **AND** restores authenticated state if valid
- **AND** shows login page if invalid/expired

#### Scenario: Session validation
- **WHEN** request arrives with session token
- **THEN** system validates session exists and is not expired
- **AND** attaches user/admin identity to request context

#### Scenario: Session logout
- **WHEN** user or admin logs out
- **THEN** system invalidates server-side session
- **AND** client clears localStorage token

#### Scenario: Invalid session token
- **WHEN** request arrives with invalid or expired session token
- **THEN** system treats request as unauthenticated
- **AND** client clears localStorage token
- **AND** shows login page

---

### Requirement: Admin Dashboard
The system SHALL provide an admin-only interface for system configuration and model management with persistent state.

#### Scenario: Access admin dashboard
- **WHEN** authenticated admin navigates to /admin
- **THEN** system displays admin dashboard with model controls

#### Scenario: Dashboard state recovery
- **WHEN** admin refreshes page with valid session
- **THEN** system recovers session from localStorage
- **AND** displays dashboard with current model status
- **AND** displays current access protection setting

#### Scenario: Configure model settings
- **WHEN** admin selects backbone, codec, and device options
- **AND** clicks load model
- **THEN** ModelManager loads model with specified configuration

#### Scenario: View model status
- **WHEN** admin views dashboard
- **THEN** system displays current model status (loaded/loading/error/unloaded)
- **AND** shows GPU memory usage if applicable

#### Scenario: Unauthenticated admin access
- **WHEN** unauthenticated user navigates to /admin
- **THEN** system displays admin login page

---

### Requirement: User Access Control
The system SHALL allow admin to enable or disable password protection for the user interface with reliable toggle behavior.

#### Scenario: Enable user access protection
- **WHEN** authenticated admin enables user access protection toggle
- **THEN** users must authenticate to access TTS functionality
- **AND** setting is persisted to users.json
- **AND** UI reflects enabled state

#### Scenario: Disable user access protection
- **WHEN** authenticated admin disables user access protection toggle
- **THEN** TTS functionality is publicly accessible without login
- **AND** setting is persisted to users.json
- **AND** UI reflects disabled state

#### Scenario: Access protection state on page load
- **WHEN** admin dashboard loads with valid session
- **THEN** access protection checkbox reflects current server-side setting

#### Scenario: User login when protection enabled
- **WHEN** user access protection is enabled
- **AND** user provides valid credentials
- **THEN** system creates authenticated session
- **AND** grants access to TTS functionality

#### Scenario: User access when protection disabled
- **WHEN** user access protection is disabled
- **THEN** users can access TTS functionality without authentication

---

## ADDED Requirements

### Requirement: User List Management
The system SHALL provide a comprehensive user list interface for admins to view and manage all registered users.

#### Scenario: View user list
- **WHEN** authenticated admin views user management section
- **THEN** system displays table with all users
- **AND** shows username, enabled status, and creation date for each user

#### Scenario: Enable user from list
- **WHEN** admin clicks enable action for a disabled user in the list
- **THEN** system enables the user
- **AND** updates the list display
- **AND** shows success confirmation

#### Scenario: Disable user from list
- **WHEN** admin clicks disable action for an enabled user in the list
- **THEN** system disables the user
- **AND** invalidates user's active sessions
- **AND** updates the list display
- **AND** shows success confirmation

#### Scenario: Remove user from list
- **WHEN** admin clicks remove action for a user in the list
- **THEN** system removes the user
- **AND** invalidates user's active sessions
- **AND** updates the list display
- **AND** shows success confirmation

#### Scenario: Empty user list
- **WHEN** no users are registered
- **THEN** system displays "No users registered" message

#### Scenario: Refresh user list
- **WHEN** admin clicks refresh button
- **THEN** system reloads user list from storage
- **AND** updates display with current data
