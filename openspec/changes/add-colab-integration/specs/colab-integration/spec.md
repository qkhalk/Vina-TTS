## ADDED Requirements

### Requirement: Colab Notebook Generation
The system SHALL generate pre-configured Google Colab notebooks that administrators can download and run to set up remote TTS backend.

#### Scenario: Download Colab notebook
- **WHEN** authenticated admin clicks "Download Notebook" button
- **THEN** system generates .ipynb file with current model configuration
- **AND** embeds unique authentication token
- **AND** triggers browser file download

#### Scenario: Notebook contains all dependencies
- **WHEN** admin runs downloaded notebook in Google Colab
- **THEN** notebook installs espeak-ng via apt-get
- **AND** installs Python dependencies via pip
- **AND** downloads model from HuggingFace
- **AND** starts FastAPI server with ngrok tunnel

#### Scenario: Notebook displays connection info
- **WHEN** notebook completes setup and starts server
- **THEN** notebook displays ngrok tunnel URL
- **AND** displays authentication token
- **AND** displays instructions for pasting into admin UI

---

### Requirement: Colab Connection Management
The system SHALL allow administrators to connect to and manage remote Colab TTS backend instances.

#### Scenario: Configure Colab endpoint
- **WHEN** authenticated admin enters Colab endpoint URL
- **AND** enters authentication token
- **AND** clicks "Connect"
- **THEN** system validates connection with health check
- **AND** saves configuration to config.yaml
- **AND** displays connection success status

#### Scenario: Invalid Colab endpoint
- **WHEN** admin enters invalid or unreachable endpoint URL
- **AND** clicks "Connect"
- **THEN** system displays connection error message
- **AND** does not save configuration

#### Scenario: Invalid authentication token
- **WHEN** admin enters correct endpoint URL but wrong token
- **AND** clicks "Connect"
- **THEN** system displays authentication error message
- **AND** does not save configuration

#### Scenario: Test Colab connection
- **WHEN** authenticated admin clicks "Test Connection" button
- **AND** Colab endpoint is configured
- **THEN** system sends health check request
- **AND** displays connection status (latency, GPU memory, model loaded)

#### Scenario: Enable Colab remote mode
- **WHEN** authenticated admin enables "Use Colab Backend" toggle
- **AND** valid Colab endpoint is configured
- **THEN** system switches ModelManager to remote mode
- **AND** TTS requests route through Colab

#### Scenario: Disable Colab remote mode
- **WHEN** authenticated admin disables "Use Colab Backend" toggle
- **THEN** system switches ModelManager to local mode
- **AND** TTS requests use local model (if loaded)

---

### Requirement: Colab API Server
The system SHALL provide a FastAPI server that runs in Google Colab to handle remote TTS requests.

#### Scenario: TTS synthesis endpoint
- **WHEN** authenticated request arrives at POST /tts/synthesize
- **WITH** valid JSON body containing text, voice sample, and options
- **THEN** server performs TTS synthesis using loaded model
- **AND** returns audio data as base64-encoded response

#### Scenario: Health check endpoint
- **WHEN** authenticated request arrives at GET /health
- **THEN** server returns status object with:
  - model loaded status
  - GPU memory usage
  - uptime seconds
  - server version

#### Scenario: Unauthorized request
- **WHEN** request arrives without valid Bearer token
- **THEN** server returns 401 Unauthorized
- **AND** does not process the request

#### Scenario: Model not loaded error
- **WHEN** TTS request arrives
- **AND** model is not loaded in Colab
- **THEN** server returns 503 Service Unavailable
- **AND** includes error message indicating model not ready

---

### Requirement: Colab TTS Client Proxy
The system SHALL provide an HTTP client that proxies TTS requests to remote Colab backend with the same interface as local model.

#### Scenario: Proxy synthesis request
- **WHEN** application calls TTS synthesis
- **AND** ModelManager is in remote mode
- **THEN** ColabTTSClient sends HTTP request to Colab endpoint
- **AND** decodes base64 audio response
- **AND** returns audio data to caller

#### Scenario: Connection timeout
- **WHEN** Colab endpoint does not respond within timeout period (60s)
- **THEN** ColabTTSClient raises TimeoutError
- **AND** returns appropriate error message

#### Scenario: Retry on transient failure
- **WHEN** Colab request fails with 5xx error
- **THEN** ColabTTSClient retries up to 2 times
- **AND** applies exponential backoff between retries

#### Scenario: Health check polling
- **WHEN** remote mode is enabled
- **THEN** ColabTTSClient polls health endpoint every 30 seconds
- **AND** updates connection status in ModelManager

---

### Requirement: Colab Configuration Persistence
The system SHALL persist Colab configuration across application restarts.

#### Scenario: Save Colab config
- **WHEN** admin successfully connects to Colab endpoint
- **THEN** system saves endpoint URL and encrypted token to config.yaml

#### Scenario: Load Colab config on startup
- **WHEN** application starts
- **AND** config.yaml contains Colab configuration
- **THEN** system loads configuration
- **AND** attempts to restore connection if endpoint was previously connected

#### Scenario: Environment variable override
- **WHEN** COLAB_ENDPOINT_URL environment variable is set
- **THEN** system uses env var value instead of config.yaml
- **AND** same applies for COLAB_AUTH_TOKEN

#### Scenario: Clear Colab config
- **WHEN** admin clicks "Disconnect" button
- **THEN** system clears Colab connection
- **AND** if backend mode was REMOTE, switches to LOCAL mode

---

### Requirement: Backend Mode Selection
The system SHALL allow administrators to choose between local and remote (Colab) backends for TTS processing.

#### Scenario: Select local backend mode
- **WHEN** admin selects "Local" in backend mode selector
- **AND** local model is loaded
- **THEN** system routes TTS requests to local model
- **AND** displays "Local" as active backend

#### Scenario: Select Colab backend mode
- **WHEN** admin selects "Google Colab" in backend mode selector
- **AND** Colab connection is established
- **THEN** system routes TTS requests to Colab
- **AND** displays "Google Colab" as active backend

#### Scenario: Cannot select unavailable backend
- **WHEN** admin selects backend mode
- **AND** selected backend is not available (local model not loaded OR Colab not connected)
- **THEN** system displays warning message
- **AND** does not change backend mode

#### Scenario: Both backends ready
- **WHEN** local model is loaded
- **AND** Colab connection is established
- **THEN** admin can switch between modes instantly
- **AND** both backends remain available

---

### Requirement: User Instructions Documentation
The system SHALL provide comprehensive documentation for setting up and using Colab integration.

#### Scenario: Documentation file exists
- **WHEN** Colab integration feature is implemented
- **THEN** `docs/colab-integration.md` file exists with setup instructions

#### Scenario: Documentation covers prerequisites
- **WHEN** user reads documentation
- **THEN** documentation lists all prerequisites (Google account, optional ngrok account)

#### Scenario: Documentation provides step-by-step guide
- **WHEN** user follows documentation
- **THEN** documentation provides numbered steps for:
  - Downloading notebook from admin UI
  - Running notebook in Google Colab
  - Copying connection URL and token
  - Configuring admin UI
  - Switching backend modes

#### Scenario: Documentation includes troubleshooting
- **WHEN** user encounters issues
- **THEN** documentation provides troubleshooting section for common problems
