import os
from openai import OpenAI
from tkinter import Tk, simpledialog, filedialog
from pathlib import Path

def convert_text_to_speech(client, text, model, voice="alloy", response_format="aac", speed=1.1):
    """
    Convert text to speech using the new OpenAI API client and latest TTS models.
    """
    try:
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            response_format=response_format,
            speed=speed,
            input=text
        )
        
        # Read the audio data
        audio_data = response.read()
        return audio_data
        
    except Exception as e:
        raise Exception(f"TTS API request failed: {str(e)}")

def process_text_file(client, text_file_path, model_choice, voice_choice):
    """
    Process a text file and convert it to speech.
    """
    # Read the file
    with open(text_file_path, 'r', encoding='utf-8') as file:
        text_content = file.read()
    
    # Check file size
    if len(text_content) > 4096:
        print(f"❌ Error: File is {len(text_content)} characters long.")
        print("This exceeds OpenAI's 4096 character limit.")
        print("Please use a shorter text file or the batch version (app_modern.py).")
        return False
    
    output_path = Path(text_file_path).with_suffix('.aac')
    
    print(f"📄 File size: {len(text_content)} characters")
    print(f"🎙️ Model: {model_choice}")
    print(f"🎭 Voice: {voice_choice}")
    print(f"📁 Output: {output_path}")
    
    try:
        response_data = convert_text_to_speech(client, text_content, model_choice, voice_choice)
        
        with open(output_path, 'wb') as file:
            file.write(response_data)
        
        print(f"✅ Successfully created audio file: {output_path}")
        print(f"📊 File size: {len(response_data)} bytes")
        return True
        
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        return False

def choose_voice_model():
    """Let user choose between the latest TTS models."""
    print("\n🎙️ Available TTS Models:")
    print("1. tts-1 (Fast, Standard Quality)")
    print("2. tts-1-hd (Slower, High Definition)")
    print("3. tts-1-1106 (Latest, Best Quality)")
    
    while True:
        choice = input("Select voice model (1-3): ").strip()
        if choice == "1":
            return "tts-1"
        elif choice == "2":
            return "tts-1-hd"
        elif choice == "3":
            return "tts-1-1106"
        else:
            print("Please enter 1, 2, or 3.")

def choose_voice():
    """Let user choose from available voices."""
    voices = {
        "1": "alloy",
        "2": "echo", 
        "3": "fable",
        "4": "onyx",
        "5": "nova",
        "6": "shimmer"
    }
    
    print("\n🎭 Available Voices:")
    for key, voice in voices.items():
        print(f"{key}. {voice.capitalize()}")
    
    while True:
        choice = input("Select voice (1-6): ").strip()
        if choice in voices:
            return voices[choice]
        else:
            print("Please enter a number between 1 and 6.")

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

def main():
    """Main function to orchestrate the TTS conversion."""
    print("🎤 Simple OpenAI Text-to-Speech Converter")
    print("=" * 45)
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("❌ API key is required.")
        return

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Select text file
    text_file_path = select_text_file()
    if not text_file_path:
        print("❌ No file selected.")
        return

    # Choose model and voice
    model_choice = choose_voice_model()
    voice_choice = choose_voice()
    
    print(f"\n🎯 Settings:")
    print(f"   Model: {model_choice}")
    print(f"   Voice: {voice_choice}")
    print(f"   Input: {text_file_path}")
    
    # Process the file
    success = process_text_file(client, text_file_path, model_choice, voice_choice)
    
    if success:
        print("\n🎉 Conversion completed successfully!")
    else:
        print("\n💥 Conversion failed. Please check the error messages above.")

if __name__ == "__main__":
    main()