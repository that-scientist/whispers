#!/usr/bin/env python3
"""
Enhanced OpenAI Text-to-Speech Converter
A comprehensive tool for converting text files to speech with advanced features.
"""

import os
import asyncio
import aiohttp
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import argparse
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tts_converter.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TTSConfig:
    """Configuration for TTS conversion."""
    model: str = "tts-1"
    voice: str = "alloy"
    response_format: str = "aac"
    speed: float = 1.1
    max_chars: int = 4096
    rate_limit_delay: float = 0.6

class TTSConverter:
    """Enhanced TTS converter with better error handling and UX."""
    
    def __init__(self, api_key: str, config: TTSConfig):
        self.api_key = api_key
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def convert_text_to_speech(self, text: str, retries: int = 3) -> bytes:
        """Convert text to speech with retry logic."""
        for attempt in range(retries):
            try:
                response = await self.session.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.config.model,
                        "voice": self.config.voice,
                        "response_format": self.config.response_format,
                        "speed": self.config.speed,
                        "input": text
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                )
                
                if response.status == 200:
                    return await response.read()
                elif response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                    continue
                else:
                    error_text = await response.text()
                    logger.error(f"API request failed: {response.status} - {error_text}")
                    if attempt == retries - 1:
                        raise Exception(f"API request failed after {retries} attempts")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            except asyncio.TimeoutError:
                logger.error(f"Request timeout on attempt {attempt + 1}")
                if attempt == retries - 1:
                    raise Exception("Request timeout after all retries")
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Request failed on attempt {attempt + 1}: {e}")
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
    
    def split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks respecting word boundaries."""
        if len(text) <= self.config.max_chars:
            return [text]
        
        chunks = []
        while text:
            if len(text) <= self.config.max_chars:
                chunks.append(text)
                break
            
            # Find the last space within the limit
            split_point = text.rfind(' ', 0, self.config.max_chars)
            if split_point == -1:
                split_point = self.config.max_chars
            
            chunks.append(text[:split_point])
            text = text[split_point:].lstrip()
        
        return chunks
    
    async def process_file(self, file_path: str, output_dir: Optional[str] = None) -> bool:
        """Process a text file and convert it to speech."""
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            logger.info(f"Processing file: {file_path}")
            logger.info(f"Text length: {len(text_content)} characters")
            
            # Split into chunks if necessary
            chunks = self.split_text_into_chunks(text_content)
            logger.info(f"Split into {len(chunks)} chunks")
            
            # Determine output path
            input_path = Path(file_path)
            if output_dir:
                output_path = Path(output_dir) / f"{input_path.stem}.{self.config.response_format}"
            else:
                output_path = input_path.with_suffix(f'.{self.config.response_format}')
            
            # Process chunks
            if len(chunks) == 1:
                logger.info("Processing single chunk...")
                audio_data = await self.convert_text_to_speech(chunks[0])
                
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                
                logger.info(f"✅ Successfully created: {output_path}")
                logger.info(f"File size: {len(audio_data)} bytes")
                
            else:
                logger.info("Processing multiple chunks...")
                temp_files = []
                
                for i, chunk in enumerate(chunks, 1):
                    logger.info(f"Processing chunk {i}/{len(chunks)}...")
                    
                    audio_data = await self.convert_text_to_speech(chunk)
                    
                    # Save temporary file
                    temp_path = output_path.with_stem(f"{output_path.stem}_temp_{i}")
                    with open(temp_path, 'wb') as f:
                        f.write(audio_data)
                    temp_files.append(temp_path)
                    
                    logger.info(f"✅ Chunk {i} saved: {temp_path}")
                    
                    # Rate limiting (except for last chunk)
                    if i < len(chunks):
                        delay = 6 if self.config.model == "tts-1-hd" else 0.6
                        logger.info(f"⏳ Waiting {delay}s for rate limit...")
                        await asyncio.sleep(delay)
                
                # Note: Audio combination would require pydub, which has dependency issues
                # For now, we'll save individual files and inform the user
                logger.info(f"✅ All chunks processed. Individual files saved:")
                for temp_file in temp_files:
                    logger.info(f"  - {temp_file}")
                logger.info("Note: Use a media player to combine the files if needed.")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing file: {e}")
            return False

class TTSInterface:
    """User interface for the TTS converter."""
    
    def __init__(self):
        self.config = TTSConfig()
    
    def get_api_key(self) -> Optional[str]:
        """Get API key from environment or user input."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Please set your OpenAI API key:")
            print("1. Set environment variable: export OPENAI_API_KEY='your-key-here'")
            print("2. Or enter it when prompted")
            api_key = input("Enter your OpenAI API key: ").strip()
        
        return api_key if api_key else None
    
    def select_model(self) -> str:
        """Let user select the TTS model."""
        print("\nAvailable models:")
        print("1. tts-1 (Normal) - Faster, lower quality")
        print("2. tts-1-hd (High Definition) - Slower, higher quality")
        
        while True:
            choice = input("Select model (1 or 2): ").strip()
            if choice == "1":
                self.config.model = "tts-1"
                self.config.rate_limit_delay = 0.6
                return "tts-1"
            elif choice == "2":
                self.config.model = "tts-1-hd"
                self.config.rate_limit_delay = 6
                return "tts-1-hd"
            else:
                print("Please enter 1 or 2.")
    
    def select_voice(self) -> str:
        """Let user select the voice."""
        voices = {
            "1": "alloy",
            "2": "echo", 
            "3": "fable",
            "4": "onyx",
            "5": "nova",
            "6": "shimmer"
        }
        
        print("\nAvailable voices:")
        for key, voice in voices.items():
            print(f"{key}. {voice.capitalize()}")
        
        while True:
            choice = input("Select voice (1-6): ").strip()
            if choice in voices:
                self.config.voice = voices[choice]
                return voices[choice]
            else:
                print("Please enter a number between 1 and 6.")
    
    def select_speed(self) -> float:
        """Let user select the speech speed."""
        print("\nSpeech speed:")
        print("1. Slow (0.75x)")
        print("2. Normal (1.0x)")
        print("3. Fast (1.25x)")
        print("4. Very Fast (1.5x)")
        
        speeds = {"1": 0.75, "2": 1.0, "3": 1.25, "4": 1.5}
        
        while True:
            choice = input("Select speed (1-4): ").strip()
            if choice in speeds:
                self.config.speed = speeds[choice]
                return speeds[choice]
            else:
                print("Please enter a number between 1 and 4.")
    
    def get_file_path(self) -> Optional[str]:
        """Get the input file path."""
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            if os.path.exists(file_path):
                return file_path
            else:
                print(f"Error: File '{file_path}' not found.")
                return None
        
        print("\nEnter the path to your text file:")
        file_path = input("File path: ").strip()
        
        if not file_path:
            return None
        
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found.")
            return None
        
        return file_path
    
    def get_output_directory(self) -> Optional[str]:
        """Get the output directory."""
        print("\nOutput options:")
        print("1. Save in same directory as input file")
        print("2. Specify custom output directory")
        
        while True:
            choice = input("Select option (1 or 2): ").strip()
            if choice == "1":
                return None
            elif choice == "2":
                output_dir = input("Enter output directory path: ").strip()
                if output_dir and not os.path.exists(output_dir):
                    try:
                        os.makedirs(output_dir)
                        return output_dir
                    except Exception as e:
                        print(f"Error creating directory: {e}")
                        return None
                return output_dir
            else:
                print("Please enter 1 or 2.")

async def main():
    """Main function."""
    print("🎤 Enhanced OpenAI Text-to-Speech Converter")
    print("=" * 50)
    
    interface = TTSInterface()
    
    # Get API key
    api_key = interface.get_api_key()
    if not api_key:
        print("❌ API key is required.")
        return
    
    # Get file path
    file_path = interface.get_file_path()
    if not file_path:
        print("❌ No valid file selected.")
        return
    
    # Configure options
    interface.select_model()
    interface.select_voice()
    interface.select_speed()
    
    # Get output directory
    output_dir = interface.get_output_directory()
    
    # Process the file
    async with TTSConverter(api_key, interface.config) as converter:
        success = await converter.process_file(file_path, output_dir)
        
        if success:
            print("\n🎉 Conversion completed successfully!")
            print(f"Check the log file 'tts_converter.log' for details.")
        else:
            print("\n💥 Conversion failed. Check the log file for details.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        print("Check the log file for more details.")