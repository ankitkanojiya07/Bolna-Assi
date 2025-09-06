# Assembly AI Transcriber Integration

This document describes the integration of Assembly AI as a transcriber (ASR) provider in the Bolna package.

## Overview

Assembly AI has been integrated as a new transcriber provider that supports real-time streaming speech-to-text transcription. This integration follows the existing Bolna architecture and patterns.

## Files Added/Modified

### New Files
- `bolna/transcriber/assemblyai_transcriber.py` - Main Assembly AI transcriber implementation
- `assemblyai_example_config.json` - Example configuration using Assembly AI
- `simple_test_assemblyai.py` - Test script to verify integration

### Modified Files
- `bolna/transcriber/__init__.py` - Added Assembly AI transcriber import
- `bolna/providers.py` - Added Assembly AI to supported transcriber providers

## Features

The Assembly AI transcriber supports:

- **Real-time streaming transcription** via WebSocket connection
- **Multiple audio formats** (linear16, mulaw)
- **Configurable sampling rates** (8kHz for telephony, 16kHz for web)
- **Language support** with configurable language codes
- **Keyword boosting** for improved accuracy
- **Interim and final transcript results**
- **Connection management** with heartbeat and error handling

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
ASSEMBLYAI_HOST=api.assemblyai.com  # Optional, defaults to api.assemblyai.com
```

### Transcriber Configuration

```json
{
  "transcriber": {
    "provider": "assemblyai",
    "model": "best",
    "language": "en",
    "stream": true,
    "encoding": "linear16",
    "sampling_rate": 16000,
    "keywords": "hello,help,thanks,goodbye"
  }
}
```

### Configuration Parameters

- `provider`: Must be set to "assemblyai"
- `model`: Assembly AI model to use (default: "best")
- `language`: Language code (default: "en")
- `stream`: Enable streaming mode (default: true)
- `encoding`: Audio encoding format ("linear16" or "mulaw")
- `sampling_rate`: Audio sample rate in Hz
- `keywords`: Comma-separated keywords for boosting accuracy

## Usage Example

```python
from bolna.transcriber.assemblyai_transcriber import AssemblyAITranscriber

# Initialize the transcriber
transcriber = AssemblyAITranscriber(
    telephony_provider="web_based_call",
    model="best",
    stream=True,
    language="en",
    sampling_rate=16000,
    encoding="linear16"
)

# Start transcription
await transcriber.transcribe()
```

## API Compatibility

The Assembly AI transcriber implements the same interface as other Bolna transcribers:

- Inherits from `BaseTranscriber`
- Implements `transcribe()` method for main transcription loop
- Supports WebSocket streaming with `sender_stream()` and `receiver()` methods
- Handles connection management and error recovery
- Provides interim and final transcript results

## Error Handling

The implementation includes comprehensive error handling for:

- WebSocket connection failures
- Authentication errors
- Network timeouts
- Connection drops and reconnection
- Invalid audio data

## Testing

Run the integration test:

```bash
python simple_test_assemblyai.py
```

This will verify:
- File structure and imports
- Provider registration
- Class method implementation
- Configuration validation

## Dependencies

The Assembly AI transcriber requires:

- `aiohttp` - For HTTP requests
- `websockets` - For WebSocket connections
- `python-dotenv` - For environment variable loading
- `pydantic` - For data validation

## Notes

- The transcriber automatically adjusts audio parameters based on the telephony provider
- WebSocket connections include heartbeat mechanisms to maintain stability
- The implementation follows Assembly AI's real-time streaming API specifications
- Error recovery includes automatic reconnection attempts

## Future Enhancements

Potential improvements for future versions:

- Support for additional Assembly AI models
- Enhanced keyword boosting configuration
- Custom audio preprocessing options
- Advanced error recovery strategies
- Performance monitoring and metrics
