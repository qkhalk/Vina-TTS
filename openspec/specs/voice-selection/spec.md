# voice-selection Specification

## Purpose
TBD - created by archiving change fix-voice-filter-for-quantized-models. Update Purpose after archive.
## Requirements
### Requirement: Model-Based Voice Filtering
The system SHALL filter available preset voices based on the currently loaded model configuration to ensure only compatible voices are presented to users.

#### Scenario: GGUF model shows limited voices
- **GIVEN** the admin has loaded a GGUF backbone model (VieNeu-TTS-q4-gguf or VieNeu-TTS-q8-gguf)
- **AND** any codec is configured (ONNX or Standard)
- **WHEN** a user accesses the client interface
- **THEN** only the 4 optimized voices SHALL be shown: "Vĩnh (nam miền Nam)", "Bình (nam miền Bắc)", "Ngọc (nữ miền Bắc)", "Dung (nữ miền Nam)"
- **AND** other voices SHALL be hidden from the dropdown

#### Scenario: Non-GGUF model shows all voices
- **GIVEN** the admin has loaded a non-GGUF backbone model (VieNeu-TTS GPU)
- **AND** any codec is configured
- **WHEN** a user accesses the client interface
- **THEN** all 9 available preset voices SHALL be shown in the dropdown
- **AND** users can select any voice

#### Scenario: Voice list updates when model changes
- **GIVEN** a user has the client interface open
- **WHEN** the admin changes the model configuration and loads a different model
- **AND** the user clicks "Refresh Status"
- **THEN** the voice dropdown SHALL update to show only voices compatible with the new model
- **AND** if the currently selected voice is no longer available, the first available voice SHALL be auto-selected

#### Scenario: Custom voice mode always available
- **GIVEN** any model configuration is loaded
- **WHEN** a user switches to "Custom Voice" tab
- **THEN** the user SHALL be able to upload their own reference audio and text
- **AND** voice filtering does not apply to custom voice mode

### Requirement: Supported Voices API
ModelManager SHALL provide an API to retrieve the list of supported voices for the currently loaded model configuration.

#### Scenario: Get supported voices for loaded model
- **GIVEN** a model is loaded with specific backbone and codec configuration
- **WHEN** `model_manager.get_supported_voices()` is called
- **THEN** it SHALL return a list of voice names that are compatible
- **AND** the list SHALL be filtered based on model type and codec type

#### Scenario: Get supported voices when no model loaded
- **GIVEN** no model is currently loaded
- **WHEN** `model_manager.get_supported_voices()` is called
- **THEN** it SHALL return all available voices from config
- **AND** no filtering SHALL be applied

### Requirement: Voice Compatibility Metadata
The system SHALL maintain metadata about which voices are compatible with GGUF backbone models.

#### Scenario: GGUF compatibility list defined
- **GIVEN** the system configuration
- **WHEN** code queries GGUF-compatible voices
- **THEN** it SHALL return exactly 4 voices: Vĩnh, Bình, Ngọc, Dung
- **AND** this list is hardcoded based on testing/optimization for GGUF models

#### Scenario: Voice has required reference files
- **GIVEN** a voice is listed in configuration
- **WHEN** the system checks for required files
- **THEN** the voice MUST have audio (.wav) and text (.txt) files at minimum
- **AND** optionally have pre-encoded codes (.pt) for ONNX codec optimization
- **AND** all referenced files MUST exist in the sample directory

