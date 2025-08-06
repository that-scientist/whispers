#!/usr/bin/env python3
"""
Test script for the enhanced TTS converter.
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
        from app_enhanced import TTSConverter, TTSConfig, TTSInterface
        print("✅ Enhanced TTS modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import enhanced TTS modules: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from app_enhanced import TTSConfig
        config = TTSConfig()
        print(f"✅ Default config created: model={config.model}, voice={config.voice}")
        return True
    except Exception as e:
        print(f"❌ Failed to create config: {e}")
        return False

def test_text_splitting():
    """Test text splitting functionality."""
    print("\nTesting text splitting...")
    
    try:
        from app_enhanced import TTSConverter, TTSConfig
        
        config = TTSConfig()
        converter = TTSConverter("dummy-key", config)
        
        # Test short text
        short_text = "This is a short text."
        chunks = converter.split_text_into_chunks(short_text)
        assert len(chunks) == 1, f"Expected 1 chunk, got {len(chunks)}"
        print("✅ Short text splitting works")
        
        # Test long text
        long_text = "This is a very long text. " * 200  # ~6000 characters
        chunks = converter.split_text_into_chunks(long_text)
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
        # Create a test file
        test_file = "test_input.txt"
        test_content = "This is a test file for the TTS converter."
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        print("✅ Test file created")
        
        # Test file reading
        with open(test_file, 'r') as f:
            content = f.read()
        
        assert content == test_content, "File content doesn't match"
        print("✅ File reading works")
        
        # Clean up
        os.remove(test_file)
        print("✅ Test file cleaned up")
        
        return True
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False

def test_interface():
    """Test the user interface components."""
    print("\nTesting interface components...")
    
    try:
        from app_enhanced import TTSInterface
        
        interface = TTSInterface()
        print("✅ Interface created successfully")
        
        # Test configuration methods
        config = interface.config
        print(f"✅ Default config: model={config.model}, voice={config.voice}")
        
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
        from app_enhanced import TTSConverter, TTSConfig
        
        config = TTSConfig()
        
        # Test context manager
        async with TTSConverter("dummy-key", config) as converter:
            print("✅ Async context manager works")
            
            # Test text splitting
            text = "Test text for async processing."
            chunks = converter.split_text_into_chunks(text)
            assert len(chunks) == 1, "Text splitting failed in async context"
            print("✅ Async text splitting works")
        
        return True
    except Exception as e:
        print(f"❌ Async components test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Enhanced TTS Converter")
    print("=" * 40)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Text Splitting", test_text_splitting),
        ("File Operations", test_file_operations),
        ("Interface", test_interface),
        ("Config File", test_config_file),
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
        print("🎉 All tests passed! The enhanced TTS converter is ready to use.")
        print("\nNext steps:")
        print("1. Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
        print("2. Run the converter: python app_enhanced.py")
        print("3. Or run batch processing: python app_batch_enhanced.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)