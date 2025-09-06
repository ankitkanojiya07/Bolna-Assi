#!/bin/bash

# Quick Start Script for Bolna with Assembly AI
# This script helps you get started quickly

echo "🚀 Bolna with Assembly AI - Quick Start"
echo "======================================"

# Check if .env file exists
if [ ! -f "local_setup/.env" ]; then
    echo "❌ .env file not found in local_setup directory"
    echo "📝 Please create local_setup/.env with your API keys:"
    echo ""
    echo "ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here"
    echo "ELEVENLABS_API_KEY=your_elevenlabs_api_key_here"
    echo "OPENAI_API_KEY=your_openai_api_key_here"
    echo "TWILIO_ACCOUNT_SID=your_twilio_account_sid"
    echo "TWILIO_AUTH_TOKEN=your_twilio_auth_token"
    echo "TWILIO_PHONE_NUMBER=your_twilio_phone_number"
    echo "REDIS_URL=redis://localhost:6379"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✅ .env file found"

# Install dependencies
echo "📦 Installing dependencies..."
pip install aiohttp websockets python-dotenv pydantic aiofiles fastapi uvicorn

# Test Assembly AI integration
echo "🧪 Testing Assembly AI integration..."
python simple_test_assemblyai.py

if [ $? -eq 0 ]; then
    echo "✅ Assembly AI integration test passed"
else
    echo "❌ Assembly AI integration test failed"
    exit 1
fi

echo ""
echo "🎯 Ready to start servers!"
echo ""
echo "To start the servers, run these commands in separate terminals:"
echo ""
echo "Terminal 1 (Bolna Server):"
echo "uvicorn local_setup.quickstart_server:app --app-dir local_setup/ --port 5001 --reload"
echo ""
echo "Terminal 2 (Twilio Server):"
echo "uvicorn local_setup.telephony_server.twilio_api_server:app --app-dir local_setup/telephony_server --port 8001 --reload"
echo ""
echo "Terminal 3 (Optional - ngrok tunnels):"
echo "ngrok http 5001"
echo "ngrok http 8001"
echo ""
echo "📖 For detailed instructions, see RUNNING_GUIDE.md"
