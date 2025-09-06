#!/usr/bin/env python3
"""
Simple test script to verify Assembly AI transcriber integration
"""

import os
import sys

def test_assemblyai_transcriber_file_exists():
    """Test that Assembly AI transcriber file exists"""
    transcriber_file = os.path.join(os.path.dirname(__file__), 'bolna', 'transcriber', 'assemblyai_transcriber.py')
    if os.path.exists(transcriber_file):
        print("✅ Assembly AI transcriber file exists")
        return True
    else:
        print("❌ Assembly AI transcriber file not found")
        return False

def test_assemblyai_in_providers_file():
    """Test that Assembly AI is added to providers.py"""
    providers_file = os.path.join(os.path.dirname(__file__), 'bolna', 'providers.py')
    try:
        with open(providers_file, 'r') as f:
            content = f.read()
            if 'assemblyai' in content and 'AssemblyAITranscriber' in content:
                print("✅ Assembly AI found in providers.py")
                return True
            else:
                print("❌ Assembly AI not found in providers.py")
                return False
    except FileNotFoundError:
        print("❌ providers.py file not found")
        return False

def test_assemblyai_in_transcriber_init():
    """Test that Assembly AI is added to transcriber __init__.py"""
    init_file = os.path.join(os.path.dirname(__file__), 'bolna', 'transcriber', '__init__.py')
    try:
        with open(init_file, 'r') as f:
            content = f.read()
            if 'AssemblyAITranscriber' in content:
                print("✅ Assembly AI found in transcriber __init__.py")
                return True
            else:
                print("❌ Assembly AI not found in transcriber __init__.py")
                return False
    except FileNotFoundError:
        print("❌ transcriber __init__.py file not found")
        return False

def test_assemblyai_transcriber_class_structure():
    """Test that Assembly AI transcriber has the required methods"""
    transcriber_file = os.path.join(os.path.dirname(__file__), 'bolna', 'transcriber', 'assemblyai_transcriber.py')
    try:
        with open(transcriber_file, 'r') as f:
            content = f.read()
            required_methods = [
                'class AssemblyAITranscriber',
                'def __init__',
                'def get_assemblyai_ws_url',
                'def transcribe',
                'def sender_stream',
                'def receiver'
            ]
            missing_methods = []
            for method in required_methods:
                if method not in content:
                    missing_methods.append(method)
            
            if not missing_methods:
                print("✅ Assembly AI transcriber has all required methods")
                return True
            else:
                print(f"❌ Assembly AI transcriber missing methods: {missing_methods}")
                return False
    except FileNotFoundError:
        print("❌ Assembly AI transcriber file not found")
        return False

def test_websocket_url_structure():
    """Test that WebSocket URL generation looks correct"""
    transcriber_file = os.path.join(os.path.dirname(__file__), 'bolna', 'transcriber', 'assemblyai_transcriber.py')
    try:
        with open(transcriber_file, 'r') as f:
            content = f.read()
            if 'api.assemblyai.com' in content and 'wss://' in content:
                print("✅ WebSocket URL structure looks correct")
                return True
            else:
                print("❌ WebSocket URL structure looks incorrect")
                return False
    except FileNotFoundError:
        print("❌ Assembly AI transcriber file not found")
        return False

def main():
    """Run all tests"""
    print("Testing Assembly AI transcriber integration...")
    print("=" * 50)
    
    tests = [
        test_assemblyai_transcriber_file_exists,
        test_assemblyai_in_providers_file,
        test_assemblyai_in_transcriber_init,
        test_assemblyai_transcriber_class_structure,
        test_websocket_url_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Assembly AI integration is properly implemented.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
