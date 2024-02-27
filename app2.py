import os
import re
import asyncio
import aiohttp
from pydub import AudioSegment
from tkinter import Tk, simpledialog, filedialog
from pathlib import Path
import time

async def convert_chunk_to_speech(session, api_key, chunk, model, voice="alloy", response_format="aac", speed="1.1"):
    response = await session.post(
        "https://api.openai.com/v1/audio/speech",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "voice": voice,
            "response_format": response_format,
            "speed": speed,
            "input": chunk
        },
    )
    response_data = await response.read()
    return response_data

def split_text(text, limit=4096):
    # Splits text into chunks that do not exceed the limit.
    # Ensure that the splitting respects word boundaries when possible.
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        else:
            # Find nearest space to the limit to avoid breaking words
            nearest_space = text.rfind(' ', 0, limit)
            if nearest_space != -1:
                chunks.append(text[:nearest_space])
                text = text[nearest_space+1:]  # Skip the space
            else:
                chunks.append(text[:limit])
                text = text[limit:]
    return chunks

async def process_text_file(api_key, text_file_path, model_choice):
    text_content = read_text_from_file(text_file_path)
    text_chunks = split_text(text_content)
    output_base_path = Path(text_file_path).with_suffix('.aac')

    # Adjust rate limit delay based on model choice
    rate_limit_delay = 0.6 if model_choice == "tts-1" else 6  # 100 RPM for tts-1, 10 RPM for tts-1-hd

    async with aiohttp.ClientSession() as session:
        for i, chunk in enumerate(text_chunks):
            response_data = await convert_chunk_to_speech(session, api_key, chunk, model_choice)
            output_path = output_base_path.with_stem(f"{output_base_path.stem}_{i+1}")
            with open(output_path, 'wb') as file:
                file.write(response_data)
            print(f"Chunk {i+1} processed. File saved: {output_path}")
            if i < len(text_chunks) - 1:  # No need to wait after the last request
                await asyncio.sleep(rate_limit_delay)

        print(f"All speech audio files have been saved based on: {output_base_path}")
        
def combine_audio_files(file_paths, output_path):
    combined = AudioSegment.empty()
    for file_path in file_paths:
        audio = AudioSegment.from_file(file_path)
        combined += audio
    combined.export(output_path, format="aac")
    
async def process_text_file(api_key, text_file_path, model_choice):
    text_content = read_text_from_file(text_file_path)
    text_chunks = split_text(text_content)
    output_base_path = Path(text_file_path).with_suffix('.aac')

    # Define rate limit delay based on model choice
    rate_limit_delay = 0.6 if model_choice == "tts-1" else 6  # 100 RPM for tts-1, 10 RPM for tts-1-hd

    output_paths = []  # Keep track of all generated file paths for combination later
    async with aiohttp.ClientSession() as session:
        for i, chunk in enumerate(text_chunks):
            response_data = await convert_chunk_to_speech(session, api_key, chunk, model_choice)
            output_path = output_base_path.with_stem(f"{output_base_path.stem}_{i+1}")
            with open(output_path, 'wb') as file:
                file.write(response_data)
            output_paths.append(output_path)
            print(f"Chunk {i+1} processed. File saved: {output_path}")
            if i < len(text_chunks) - 1:
                await asyncio.sleep(rate_limit_delay)

    # Combine all audio files into a single file
    final_output_path = output_base_path.with_stem(f"{output_base_path.stem}_combined")
    combine_audio_files(output_paths, final_output_path)
    print(f"All speech audio files have been combined into: {final_output_path}")

def choose_voice_model():
    choice = input("Select voice model - Normal (1) or High Definition (2): ").strip()
    return "tts-1-hd" if choice == "2" else "tts-1"

def get_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        root = Tk()
        root.withdraw()
        api_key = simpledialog.askstring("API Key", "Enter your OpenAI API key:", parent=root)
    return api_key

def select_text_file():
    Tk().withdraw()
    file_path = filedialog.askopenfilename()
    return file_path

def read_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

async def main():
    api_key = get_api_key()
    if not api_key:
        print("API key is required.")
        return

    text_file_path = select_text_file()
    if text_file_path:
        model_choice = choose_voice_model()
        await process_text_file(api_key, text_file_path, model_choice)
    else:
        print("No file selected.")

if __name__ == "__main__":
    asyncio.run(main())

