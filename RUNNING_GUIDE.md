# How to Run Bolna with Assembly AI Integration

## Prerequisites

1. **Python 3.10.13** (recommended)
2. **API Keys** for the services you want to use
3. **ngrok** for local tunneling (optional but recommended for testing)

## Step 1: Environment Setup

### 1.1 Create Environment File

Create a `.env` file in the `local_setup` directory with the following content:

```bash
# Assembly AI (ASR) - Required for Assembly AI transcriber
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
ASSEMBLYAI_HOST=api.assemblyai.com

# ElevenLabs (TTS) - Text-to-speech
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# OpenAI (LLM) - Language model
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# Twilio (Telephony) - Phone calls
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Redis (Caching) - Local development
REDIS_URL=redis://localhost:6379
```

### 1.2 Get API Keys

- **Assembly AI**: Sign up at [assemblyai.com](https://www.assemblyai.com/) and get your API key
- **ElevenLabs**: Sign up at [elevenlabs.io](https://elevenlabs.io/) and get your API key
- **OpenAI**: Get your API key from [platform.openai.com](https://platform.openai.com/)
- **Twilio**: Sign up at [twilio.com](https://www.twilio.com/) and get your credentials

## Step 2: Install Dependencies

```bash
# Navigate to the bolna directory
cd bolna

# Install the package
pip install -e .

# Or install specific dependencies
pip install aiohttp websockets python-dotenv pydantic aiofiles fastapi uvicorn
```

## Step 3: Start the Servers

### 3.1 Start Bolna Server (Port 5001)

```bash
# From the bolna directory
uvicorn local_setup.quickstart_server:app --app-dir local_setup/ --port 5001 --reload
```

### 3.2 Start Twilio Server (Port 8001)

```bash
# In a new terminal
uvicorn local_setup.telephony_server.twilio_api_server:app --app-dir local_setup/telephony_server --port 8001 --reload
```

### 3.3 Start Redis (Optional but recommended)

```bash
# Install Redis if not already installed
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# macOS: brew install redis
# Linux: sudo apt-get install redis-server

# Start Redis
redis-server
```

## Step 4: Set Up ngrok Tunnels (Optional)

Install ngrok and create tunnels for both servers:

```bash
# Install ngrok
# Download from https://ngrok.com/download

# Create tunnels
ngrok http 5001  # For Bolna server
ngrok http 8001  # For Twilio server
```

Note the ngrok URLs (e.g., `https://abc123.ngrok.io`) for the next step.

## Step 5: Create an Agent with Assembly AI

### 5.1 Create Agent API Call

Use this API call to create an agent with Assembly AI transcriber:

```bash
curl --location 'http://localhost:5001/agent' \
--header 'Content-Type: application/json' \
--data '{
  "agent_name": "Assembly AI Test Agent",
  "agent_type": "simple_llm_agent",
  "agent_welcome_message": "Hello! I am using Assembly AI for speech recognition. How can I help you today?",
  "tasks": [
    {
      "tools_config": {
        "transcriber": {
          "provider": "assemblyai",
          "model": "best",
          "language": "en",
          "stream": true,
          "encoding": "linear16",
          "sampling_rate": 16000,
          "keywords": "hello,help,thanks,goodbye"
        },
        "synthesizer": {
          "provider": "elevenlabs",
          "stream": true,
          "buffer_size": 100.0,
          "audio_format": "wav",
          "provider_config": {
            "voice": "George",
            "model": "eleven_turbo_v2_5",
            "voice_id": "JBFqnCBsd6RMkjVDRZzb"
          }
        },
        "llm_config": {
          "model": "gpt-3.5-turbo",
          "max_tokens": 100,
          "temperature": 0.1,
          "provider": "openai"
        }
      },
      "toolchain": {
        "execution": "parallel",
        "pipelines": [
          ["transcriber"],
          ["llm_config"],
          ["synthesizer"]
        ]
      },
      "task_type": "conversation",
      "task_config": {
        "optimize_latency": true,
        "hangup_after_silence": 20,
        "incremental_delay": 900,
        "number_of_words_for_interruption": 1,
        "interruption_backoff_period": 100,
        "hangup_after_LLMCall": false,
        "backchanneling": false,
        "ambient_noise": false,
        "call_terminate": 90,
        "use_fillers": false,
        "trigger_user_online_message_after": 10,
        "check_user_online_message": "Hey, are you still there",
        "check_if_user_online": true,
        "generate_precise_transcript": false
      }
    }
  ]
}'
```

This will return an `agent_id` that you'll use in the next step.

### 5.2 Make a Test Call

```bash
curl --location 'http://localhost:8001/call' \
--header 'Content-Type: application/json' \
--data '{
  "agent_id": "<agent_id_from_step_5.1>",
  "recipient_phone_number": "<phone-number-with-country-code>"
}'
```

## Step 6: Test the Integration

1. **Your phone should ring** - answer the call
2. **Speak naturally** - Assembly AI will transcribe your speech
3. **Listen to the response** - ElevenLabs will synthesize the AI's response
4. **Have a conversation** - test the full pipeline

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```bash
   pip install -r requirements.txt
   ```

2. **API key errors**
   - Verify your API keys are correct in the `.env` file
   - Check that the environment variables are loaded

3. **Connection errors**
   - Ensure all servers are running on the correct ports
   - Check firewall settings

4. **Assembly AI specific issues**
   - Verify your Assembly AI API key is valid
   - Check that you have sufficient credits in your Assembly AI account

### Testing Assembly AI Integration

Run the integration test:

```bash
python simple_test_assemblyai.py
```

This will verify that Assembly AI is properly integrated.

## Configuration Options

### Assembly AI Transcriber Options

```json
{
  "transcriber": {
    "provider": "assemblyai",
    "model": "best",                    // Assembly AI model
    "language": "en",                   // Language code
    "stream": true,                     // Enable streaming
    "encoding": "linear16",             // Audio encoding
    "sampling_rate": 16000,            // Sample rate
    "keywords": "hello,help,thanks"     // Keywords for boosting
  }
}
```

### Available Models
- `best` - Highest accuracy (default)
- `nano` - Fastest processing
- `conversationalai` - Optimized for conversations

### Supported Languages
- `en` - English (default)
- `es` - Spanish
- `fr` - French
- `de` - German
- And many more...

## Next Steps

1. **Customize the agent** - Modify the prompts and responses
2. **Add more features** - Implement additional tools and capabilities
3. **Scale up** - Deploy to production with proper infrastructure
4. **Monitor performance** - Use logging and analytics to optimize

## Support

- **Bolna Documentation**: Check the main README.md
- **Assembly AI Docs**: [docs.assemblyai.com](https://www.assemblyai.com/docs)
- **Issues**: Report problems in the Bolna GitHub repository
