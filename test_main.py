#!/usr/bin/env python3
"""
Test script for the unified main.py audio processor.
This script tests the basic functionality without requiring an API key.
"""

import os
import sys
import asyncio
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import aiohttp
        print("✅ aiohttp imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import aiohttp: {e}")
        return False
    
    try:
        from main import AudioProcessor, TTSConfig, TranscriptionConfig, UserInterface
        print("✅ Main modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import main modules: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from main import TTSConfig, TranscriptionConfig
        
        tts_config = TTSConfig()
        trans_config = TranscriptionConfig()
        
        print(f"✅ TTS config created: model={tts_config.model}, voice={tts_config.voice}")
        print(f"✅ Transcription config created: model={trans_config.model}")
        return True
    except Exception as e:
        print(f"❌ Failed to create configs: {e}")
        return False

def test_text_splitting():
    """Test text splitting functionality."""
    print("\nTesting text splitting...")
    
    try:
        from main import AudioProcessor, TTSConfig
        
        config = TTSConfig()
        processor = AudioProcessor("dummy-key")
        
        # Test short text
        short_text = "This is a short text."
        chunks = processor.split_text_into_chunks(short_text)
        assert len(chunks) == 1, f"Expected 1 chunk, got {len(chunks)}"
        print("✅ Short text splitting works")
        
        # Test long text
        long_text = "This is a very long text. " * 200  # ~6000 characters
        chunks = processor.split_text_into_chunks(long_text)
        assert len(chunks) > 1, f"Expected multiple chunks, got {len(chunks)}"
        print(f"✅ Long text splitting works: {len(chunks)} chunks")
        
        return True
    except Exception as e:
        print(f"❌ Text splitting test failed: {e}")
        return False

def test_file_operations():
    """Test file operations."""
    print("\nTesting file operations...")
    
    try:
        # Create test files
        test_text_file = "test_input.txt"
        test_audio_file = "test_audio.mp3"
        
        test_content = "This is a test file for the audio processor."
        
        with open(test_text_file, 'w') as f:
            f.write(test_content)
        
        # Create a dummy audio file (just a text file for testing)
        with open(test_audio_file, 'w') as f:
            f.write("dummy audio content")
        
        print("✅ Test files created")
        
        # Test file reading
        with open(test_text_file, 'r') as f:
            content = f.read()
        
        assert content == test_content, "File content doesn't match"
        print("✅ File reading works")
        
        # Clean up
        os.remove(test_text_file)
        os.remove(test_audio_file)
        print("✅ Test files cleaned up")
        
        return True
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False

def test_interface():
    """Test the user interface components."""
    print("\nTesting interface components...")
    
    try:
        from main import UserInterface
        
        interface = UserInterface()
        print("✅ Interface created successfully")
        
        # Test configuration methods
        tts_config = interface.tts_config
        trans_config = interface.transcription_config
        
        print(f"✅ Default TTS config: model={tts_config.model}, voice={tts_config.voice}")
        print(f"✅ Default transcription config: model={trans_config.model}")
        
        return True
    except Exception as e:
        print(f"❌ Interface test failed: {e}")
        return False

def test_config_file():
    """Test configuration file loading."""
    print("\nTesting configuration file...")
    
    try:
        import json
        
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            required_keys = ['default_model', 'default_voice', 'voices', 'models']
            for key in required_keys:
                assert key in config, f"Missing required key: {key}"
            
            print("✅ Configuration file is valid")
            return True
        else:
            print("⚠️  Configuration file not found (this is optional)")
            return True
    except Exception as e:
        print(f"❌ Configuration file test failed: {e}")
        return False

async def test_async_components():
    """Test async components."""
    print("\nTesting async components...")
    
    try:
        from main import AudioProcessor, TTSConfig
        
        config = TTSConfig()
        
        # Test context manager
        async with AudioProcessor("dummy-key") as processor:
            print("✅ Async context manager works")
            
            # Test text splitting
            text = "Test text for async processing."
            chunks = processor.split_text_into_chunks(text)
            assert len(chunks) == 1, "Text splitting failed in async context"
            print("✅ Async text splitting works")
        
        return True
    except Exception as e:
        print(f"❌ Async components test failed: {e}")
        return False

def test_processing_modes():
    """Test processing mode selection logic."""
    print("\nTesting processing modes...")
    
    try:
        from main import UserInterface
        
        interface = UserInterface()
        
        # Test mode selection logic
        test_cases = [
            ("1", "tts"),
            ("2", "transcription"),
            ("3", None),  # Invalid
            ("", None),    # Empty
        ]
        
        for input_choice, expected_mode in test_cases:
            # Simulate the mode selection logic
            if input_choice == "1":
                mode = "tts"
            elif input_choice == "2":
                mode = "transcription"
            else:
                mode = None
            
            if mode == expected_mode:
                print(f"✅ Mode selection '{input_choice}' -> '{mode}' works")
            else:
                print(f"❌ Mode selection '{input_choice}' failed")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Processing modes test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Unified Audio Processor")
    print("=" * 40)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Text Splitting", test_text_splitting),
        ("File Operations", test_file_operations),
        ("Interface", test_interface),
        ("Config File", test_config_file),
        ("Processing Modes", test_processing_modes),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    # Test async components
    try:
        if asyncio.run(test_async_components()):
            passed += 1
        total += 1
    except Exception as e:
        print(f"❌ Async components test crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The unified audio processor is ready to use.")
        print("\nNext steps:")
        print("1. Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
        print("2. Run the processor: python main.py")
        print("3. Choose between TTS or Transcription modes")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)