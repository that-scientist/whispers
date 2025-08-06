#!/usr/bin/env python3
"""
Example usage of the enhanced TTS converter.
This script demonstrates how to use the converter programmatically.
"""

import asyncio
import os
from app_enhanced import TTSConverter, TTSConfig

async def example_single_file():
    """Example: Convert a single text file to speech."""
    print("🎤 Example: Single File Conversion")
    print("=" * 40)
    
    # Create a sample text file
    sample_text = """
    This is a sample text for testing the enhanced TTS converter.
    It demonstrates how to convert text to speech using OpenAI's API.
    The converter supports multiple voices, speeds, and quality levels.
    """
    
    with open("sample.txt", "w") as f:
        f.write(sample_text)
    
    # Configure TTS settings
    config = TTSConfig(
        model="tts-1",  # Use fast model for testing
        voice="alloy",  # Neutral voice
        speed=1.0,      # Normal speed
        response_format="aac"
    )
    
    # Get API key (you need to set this)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-key-here'")
        return
    
    try:
        # Convert the file
        async with TTSConverter(api_key, config) as converter:
            success = await converter.process_file("sample.txt")
            
            if success:
                print("✅ Conversion completed successfully!")
                print("Check 'sample.aac' for the output file.")
            else:
                print("❌ Conversion failed.")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean up sample file
        if os.path.exists("sample.txt"):
            os.remove("sample.txt")

async def example_batch_processing():
    """Example: Process multiple files with different settings."""
    print("\n🎤 Example: Batch Processing")
    print("=" * 40)
    
    # Create sample files
    files_content = {
        "document1.txt": "This is the first document for batch processing.",
        "document2.txt": "This is the second document with different content.",
        "document3.txt": "This is the third document to demonstrate batch capabilities."
    }
    
    for filename, content in files_content.items():
        with open(filename, "w") as f:
            f.write(content)
    
    # Configure settings for batch processing
    config = TTSConfig(
        model="tts-1",
        voice="nova",  # Bright, energetic voice
        speed=1.25,    # Fast speed
        response_format="aac"
    )
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set your OpenAI API key")
        return
    
    try:
        # Process each file
        async with TTSConverter(api_key, config) as converter:
            for filename in files_content.keys():
                print(f"Processing {filename}...")
                success = await converter.process_file(filename)
                
                if success:
                    print(f"✅ {filename} processed successfully")
                else:
                    print(f"❌ {filename} failed")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean up sample files
        for filename in files_content.keys():
            if os.path.exists(filename):
                os.remove(filename)

def example_configuration():
    """Example: Show different configuration options."""
    print("\n🎤 Example: Configuration Options")
    print("=" * 40)
    
    # Different voice configurations
    voices = {
        "Professional": TTSConfig(voice="onyx", speed=1.0),
        "Storytelling": TTSConfig(voice="fable", speed=0.9),
        "Energetic": TTSConfig(voice="nova", speed=1.25),
        "High Quality": TTSConfig(model="tts-1-hd", voice="alloy", speed=1.0)
    }
    
    for name, config in voices.items():
        print(f"{name}:")
        print(f"  Model: {config.model}")
        print(f"  Voice: {config.voice}")
        print(f"  Speed: {config.speed}x")
        print(f"  Format: {config.response_format}")
        print()

def example_text_splitting():
    """Example: Demonstrate text splitting for large files."""
    print("\n🎤 Example: Text Splitting")
    print("=" * 40)
    
    # Create a long text file
    long_text = "This is a very long sentence that will be repeated many times. " * 100
    
    with open("long_document.txt", "w") as f:
        f.write(long_text)
    
    config = TTSConfig()
    converter = TTSConverter("dummy-key", config)
    
    # Split the text
    chunks = converter.split_text_into_chunks(long_text)
    print(f"Original text length: {len(long_text)} characters")
    print(f"Split into {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}: {len(chunk)} characters")
    
    # Clean up
    if os.path.exists("long_document.txt"):
        os.remove("long_document.txt")

async def main():
    """Run all examples."""
    print("📚 Enhanced TTS Converter - Usage Examples")
    print("=" * 50)
    
    # Show configuration options
    example_configuration()
    
    # Show text splitting
    example_text_splitting()
    
    # Note: The actual conversion examples require an API key
    print("\n⚠️  Note: The following examples require a valid OpenAI API key.")
    print("Set your API key with: export OPENAI_API_KEY='your-key-here'")
    print()
    
    # Uncomment the following lines to run actual conversion examples
    # await example_single_file()
    # await example_batch_processing()
    
    print("✅ Examples completed!")
    print("\nTo run the actual converter:")
    print("1. Set your API key: export OPENAI_API_KEY='your-key-here'")
    print("2. Run: python app_enhanced.py")
    print("3. Or run batch processing: python app_batch_enhanced.py")

if __name__ == "__main__":
    asyncio.run(main())