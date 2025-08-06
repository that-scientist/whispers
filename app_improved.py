import os
import asyncio
import aiohttp
from tkinter import Tk, simpledialog, filedialog
from pathlib import Path

async def convert_file_to_speech(session, api_key, file_path, model, voice="alloy", response_format="aac", speed="1.1"):
    """
    Upload the entire text file to OpenAI's TTS API and get back a single audio file.
    This is much more efficient than manually chunking the text.
    """
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as file:
        text_content = file.read()
    
    # Check if content is within OpenAI's limits (4096 characters for TTS)
    if len(text_content) > 4096:
        print(f"Warning: Text file is {len(text_content)} characters long, which exceeds OpenAI's 4096 character limit.")
        print("The API will automatically truncate the text to 4096 characters.")
        print("Consider splitting your content into smaller files for complete processing.")
    
    response = await session.post(
        "https://api.openai.com/v1/audio/speech",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "voice": voice,
            "response_format": response_format,
            "speed": speed,
            "input": text_content
        },
    )
    
    if response.status != 200:
        error_text = await response.text()
        raise Exception(f"API request failed with status {response.status}: {error_text}")
    
    response_data = await response.read()
    return response_data

async def process_text_file(api_key, text_file_path, model_choice):
    """
    Process a text file and convert it to speech in a single API call.
    """
    output_path = Path(text_file_path).with_suffix('.aac')
    
    print(f"Converting {text_file_path} to speech...")
    print(f"Model: {model_choice}")
    print(f"Output: {output_path}")
    
    async with aiohttp.ClientSession() as session:
        try:
            response_data = await convert_file_to_speech(session, api_key, text_file_path, model_choice)
            
            with open(output_path, 'wb') as file:
                file.write(response_data)
            
            print(f"✅ Successfully created audio file: {output_path}")
            print(f"File size: {len(response_data)} bytes")
            
        except Exception as e:
            print(f"❌ Error processing file: {e}")
            return False
    
    return True

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
    print("🎤 OpenAI Text-to-Speech Converter")
    print("=" * 40)
    
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
    success = await process_text_file(api_key, text_file_path, model_choice)
    
    if success:
        print("\n🎉 Conversion completed successfully!")
    else:
        print("\n💥 Conversion failed. Please check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())