## MODIFIED Requirements

### Requirement: Admin Dashboard
The system SHALL provide an admin-only interface for system configuration and model management with persistent state, including backend selection between local and remote (Colab) modes.

#### Scenario: Access admin dashboard
- **WHEN** authenticated admin navigates to /admin
- **THEN** system displays admin dashboard with model controls
- **AND** displays backend selection panel

#### Scenario: Dashboard state recovery
- **WHEN** admin refreshes page with valid session
- **THEN** system recovers session from localStorage
- **AND** displays dashboard with current model status
- **AND** displays current access protection setting
- **AND** displays current backend mode (Local or Colab)
- **AND** displays Colab connection status if configured

#### Scenario: Configure model settings
- **WHEN** admin selects backbone, codec, and device options
- **AND** clicks load model
- **THEN** ModelManager loads model with specified configuration
- **AND** model is available for local backend mode

#### Scenario: View model status
- **WHEN** admin views dashboard
- **THEN** system displays current model status (loaded/loading/error/unloaded)
- **AND** shows GPU memory usage if applicable
- **AND** shows active backend mode with visual indicator

#### Scenario: Unauthenticated admin access
- **WHEN** unauthenticated user navigates to /admin
- **THEN** system displays admin login page

#### Scenario: Access backend selection panel
- **WHEN** authenticated admin views dashboard
- **THEN** system displays Backend Selection panel with:
  - Backend mode selector (Local / Google Colab)
  - Local backend status
  - Colab connection controls and status

---

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

#### Scenario: Switch to remote backend mode
- **WHEN** admin selects "Google Colab" backend mode
- **AND** Colab connection is established
- **THEN** ModelManager switches to remote mode
- **AND** TTS requests are proxied to Colab runtime
- **AND** local model remains loaded (if previously loaded)

#### Scenario: Switch to local backend mode
- **WHEN** admin selects "Local" backend mode
- **AND** local model is loaded
- **THEN** ModelManager switches to local mode
- **AND** TTS requests use local model
- **AND** Colab connection remains active (if previously connected)

#### Scenario: Backend mode indicator
- **WHEN** admin views dashboard
- **THEN** system displays clear visual indicator of active backend mode
- **AND** shows status of both local model and Colab connection

#### Scenario: Remote backend health check
- **WHEN** Colab connection is established
- **THEN** system periodically checks Colab health endpoint
- **AND** updates connection status in admin dashboard

#### Scenario: Colab disconnect handling
- **WHEN** Colab endpoint becomes unreachable
- **AND** backend mode is REMOTE
- **THEN** system displays connection lost warning
- **AND** admin can manually switch to local mode if available
