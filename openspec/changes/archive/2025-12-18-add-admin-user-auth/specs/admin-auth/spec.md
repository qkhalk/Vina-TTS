## ADDED Requirements

### Requirement: Centralized Model Management
The system SHALL provide a singleton ModelManager that controls the TTS model lifecycle, ensuring only one model instance exists regardless of concurrent users.

#### Scenario: Model load by admin
- **WHEN** admin requests model load with valid configuration
- **THEN** ModelManager loads the model if not already loaded
- **AND** returns success status with model info

#### Scenario: Model already loaded
- **WHEN** admin requests model load while model is already loaded
- **THEN** ModelManager returns current model status without reloading

#### Scenario: Model unload
- **WHEN** admin requests model unload
- **THEN** ModelManager unloads the model and frees GPU/CPU memory
- **AND** returns success status

#### Scenario: Model restart
- **WHEN** admin requests model restart
- **THEN** ModelManager unloads current model, cleans memory, and loads fresh instance
- **AND** returns success status with new model info

#### Scenario: Concurrent load requests
- **WHEN** multiple load requests arrive simultaneously
- **THEN** ModelManager processes them sequentially using thread locks
- **AND** only one model instance is created

---

### Requirement: Admin Authentication
The system SHALL protect the admin interface with password authentication using environment variable configuration.

#### Scenario: Valid admin login
- **WHEN** user provides correct admin password from ADMIN_PASSWORD env var
- **THEN** system creates authenticated session
- **AND** redirects to admin dashboard

#### Scenario: Invalid admin login
- **WHEN** user provides incorrect admin password
- **THEN** system rejects authentication
- **AND** displays error message

#### Scenario: Missing admin password env var
- **WHEN** ADMIN_PASSWORD environment variable is not set
- **THEN** system refuses to start
- **AND** logs error message with setup instructions

#### Scenario: Admin session expiry
- **WHEN** admin session exceeds 24 hours
- **THEN** system invalidates session
- **AND** requires re-authentication

---

### Requirement: Admin Dashboard
The system SHALL provide an admin-only interface for system configuration and model management.

#### Scenario: Access admin dashboard
- **WHEN** authenticated admin navigates to /admin
- **THEN** system displays admin dashboard with model controls

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
- **THEN** system redirects to admin login page

---

### Requirement: User Access Control
The system SHALL allow admin to enable or disable password protection for the user interface.

#### Scenario: Enable user access protection
- **WHEN** admin enables user access protection
- **THEN** users must authenticate to access TTS functionality
- **AND** setting is persisted to users.json

#### Scenario: Disable user access protection
- **WHEN** admin disables user access protection
- **THEN** TTS functionality is publicly accessible without login
- **AND** setting is persisted to users.json

#### Scenario: User login when protection enabled
- **WHEN** user access protection is enabled
- **AND** user provides valid credentials
- **THEN** system creates authenticated session
- **AND** grants access to TTS functionality

#### Scenario: User access when protection disabled
- **WHEN** user access protection is disabled
- **THEN** users can access TTS functionality without authentication

---

### Requirement: User Management
The system SHALL allow admin to manage user accounts via JSON file storage.

#### Scenario: Add new user
- **WHEN** admin creates new user with username and password
- **THEN** system stores user with bcrypt-hashed password in users.json
- **AND** confirms user creation

#### Scenario: Remove user
- **WHEN** admin deletes existing user
- **THEN** system removes user from users.json
- **AND** invalidates any active sessions for that user

#### Scenario: Enable/disable user
- **WHEN** admin toggles user enabled status
- **THEN** system updates user record in users.json
- **AND** disabled users cannot authenticate

#### Scenario: Duplicate username
- **WHEN** admin attempts to create user with existing username
- **THEN** system rejects creation
- **AND** displays error message

---

### Requirement: User Interface
The system SHALL provide a simplified user interface for TTS synthesis without system configuration options.

#### Scenario: Access user page when model loaded
- **WHEN** user accesses / endpoint
- **AND** model is loaded
- **THEN** system displays TTS synthesis interface with voice selection and text input

#### Scenario: Access user page when model not loaded
- **WHEN** user accesses / endpoint
- **AND** model is not loaded
- **THEN** system displays "Service temporarily unavailable" message
- **AND** hides synthesis controls

#### Scenario: User synthesis request
- **WHEN** authenticated user (or any user if protection disabled) submits synthesis request
- **AND** model is loaded
- **THEN** system processes request using shared ModelManager
- **AND** returns generated audio

#### Scenario: User cannot configure model
- **WHEN** user views user interface
- **THEN** backbone, codec, and device configuration options are NOT displayed

---

### Requirement: Session Management
The system SHALL manage user and admin sessions securely using server-side storage.

#### Scenario: Session creation
- **WHEN** user or admin authenticates successfully
- **THEN** system creates server-side session
- **AND** sets secure HTTP-only cookie

#### Scenario: Session validation
- **WHEN** request arrives with session cookie
- **THEN** system validates session exists and is not expired
- **AND** attaches user/admin identity to request context

#### Scenario: Session logout
- **WHEN** user or admin logs out
- **THEN** system invalidates server-side session
- **AND** clears session cookie

#### Scenario: Invalid session cookie
- **WHEN** request arrives with invalid or expired session cookie
- **THEN** system treats request as unauthenticated
- **AND** redirects to appropriate login page

---

### Requirement: Lightweight Storage
The system SHALL use JSON file storage for user credentials without requiring external databases.

#### Scenario: Read users on startup
- **WHEN** application starts
- **THEN** system loads users.json into memory
- **AND** validates file structure

#### Scenario: Write users on change
- **WHEN** user is added, removed, or modified
- **THEN** system writes updated data to users.json atomically
- **AND** creates backup of previous version

#### Scenario: Missing users.json
- **WHEN** users.json does not exist
- **THEN** system creates default file with access_enabled=false and empty users array

#### Scenario: Corrupted users.json
- **WHEN** users.json contains invalid JSON
- **THEN** system logs error
- **AND** attempts to restore from backup if available
- **AND** falls back to empty state if no backup
