import os
import asyncio
import aiohttp
from pydub import AudioSegment
from tkinter import Tk, simpledialog, filedialog
from pathlib import Path

async def convert_text_to_speech(session, api_key, text, model, voice="alloy", response_format="aac", speed="1.1"):
    """
    Convert a text chunk to speech using OpenAI's TTS API.
    """
    response = await session.post(
        "https://api.openai.com/v1/audio/speech",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "voice": voice,
            "response_format": response_format,
            "speed": speed,
            "input": text
        },
    )
    
    if response.status != 200:
        error_text = await response.text()
        raise Exception(f"API request failed with status {response.status}: {error_text}")
    
    response_data = await response.read()
    return response_data

def split_text_into_chunks(text, max_chars=4096):
    """
    Split text into chunks that respect word boundaries and stay within OpenAI's limits.
    """
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    while text:
        if len(text) <= max_chars:
            chunks.append(text)
            break
        
        # Find the last space within the limit to avoid breaking words
        split_point = text.rfind(' ', 0, max_chars)
        if split_point == -1:
            # No space found, force split at max_chars
            split_point = max_chars
        
        chunks.append(text[:split_point])
        text = text[split_point:].lstrip()  # Remove leading whitespace
    
    return chunks

async def process_large_text_file(api_key, text_file_path, model_choice):
    """
    Process a text file that may be larger than OpenAI's 4096 character limit.
    Automatically splits into chunks and combines the audio files.
    """
    # Read the file
    with open(text_file_path, 'r', encoding='utf-8') as file:
        text_content = file.read()
    
    # Split into chunks if necessary
    chunks = split_text_into_chunks(text_content)
    
    print(f"📄 File size: {len(text_content)} characters")
    print(f"📦 Split into {len(chunks)} chunks")
    
    if len(chunks) == 1:
        print("✅ File fits within OpenAI's limits - processing in single request")
        return await process_single_chunk(api_key, text_file_path, model_choice, text_content)
    else:
        print("🔄 File exceeds limits - processing in batches")
        return await process_multiple_chunks(api_key, text_file_path, model_choice, chunks)

async def process_single_chunk(api_key, text_file_path, model_choice, text_content):
    """
    Process a single chunk (file fits within limits).
    """
    output_path = Path(text_file_path).with_suffix('.aac')
    
    async with aiohttp.ClientSession() as session:
        try:
            response_data = await convert_text_to_speech(session, api_key, text_content, model_choice)
            
            with open(output_path, 'wb') as file:
                file.write(response_data)
            
            print(f"✅ Successfully created audio file: {output_path}")
            print(f"📊 File size: {len(response_data)} bytes")
            return True
            
        except Exception as e:
            print(f"❌ Error processing file: {e}")
            return False

async def process_multiple_chunks(api_key, text_file_path, model_choice, chunks):
    """
    Process multiple chunks and combine them into a single audio file.
    """
    output_base_path = Path(text_file_path).with_suffix('.aac')
    temp_files = []
    
    # Rate limit delays
    rate_limit_delay = 0.6 if model_choice == "tts-1" else 6
    
    async with aiohttp.ClientSession() as session:
        try:
            # Process each chunk
            for i, chunk in enumerate(chunks):
                print(f"🔄 Processing chunk {i+1}/{len(chunks)}...")
                
                response_data = await convert_text_to_speech(session, api_key, chunk, model_choice)
                
                # Save temporary file
                temp_path = output_base_path.with_stem(f"{output_base_path.stem}_temp_{i+1}")
                with open(temp_path, 'wb') as file:
                    file.write(response_data)
                temp_files.append(temp_path)
                
                print(f"✅ Chunk {i+1} saved: {temp_path}")
                
                # Rate limiting (except for last chunk)
                if i < len(chunks) - 1:
                    print(f"⏳ Waiting {rate_limit_delay}s for rate limit...")
                    await asyncio.sleep(rate_limit_delay)
            
            # Combine all audio files
            print("🔗 Combining audio files...")
            combined = AudioSegment.empty()
            for temp_file in temp_files:
                audio = AudioSegment.from_file(temp_file)
                combined += audio
            
            # Save final combined file
            final_output_path = output_base_path.with_stem(f"{output_base_path.stem}_combined")
            combined.export(final_output_path, format="aac")
            
            print(f"✅ Successfully created combined audio file: {final_output_path}")
            print(f"📊 Combined file size: {len(combined.raw_data)} bytes")
            
            # Clean up temporary files
            for temp_file in temp_files:
                temp_file.unlink()
            
            return True
            
        except Exception as e:
            print(f"❌ Error processing chunks: {e}")
            # Clean up temporary files on error
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()
            return False

def choose_voice_model():
    """Let user choose between normal and high-definition models."""
    while True:
        choice = input("Select voice model - Normal (1) or High Definition (2): ").strip()
        if choice == "1":
            return "tts-1"
        elif choice == "2":
            return "tts-1-hd"
        else:
            print("Please enter 1 or 2.")

def get_api_key():
    """Get API key from environment or user input."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        root = Tk()
        root.withdraw()
        api_key = simpledialog.askstring("API Key", "Enter your OpenAI API key:", parent=root)
    return api_key

def select_text_file():
    """Open file dialog to select a text file."""
    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select a text file to convert to speech",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    return file_path

async def main():
    """Main function to orchestrate the TTS conversion."""
    print("🎤 OpenAI Text-to-Speech Converter (Batch Mode)")
    print("=" * 50)
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("❌ API key is required.")
        return

    # Select text file
    text_file_path = select_text_file()
    if not text_file_path:
        print("❌ No file selected.")
        return

    # Choose model
    model_choice = choose_voice_model()
    
    # Process the file
    success = await process_large_text_file(api_key, text_file_path, model_choice)
    
    if success:
        print("\n🎉 Conversion completed successfully!")
    else:
        print("\n💥 Conversion failed. Please check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())