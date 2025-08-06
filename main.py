#!/usr/bin/env python3
"""
Unified OpenAI Audio Processing Tool
Supports both real-time TTS and batch transcription with file upload.
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
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('audio_processor.log'),
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

@dataclass
class TranscriptionConfig:
    """Configuration for batch transcription."""
    model: str = "whisper-1"
    response_format: str = "verbose_json"
    language: Optional[str] = None
    prompt: Optional[str] = None
    temperature: float = 0.0

class AudioProcessor:
    """Unified audio processor for TTS and transcription."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    # TTS Methods
    async def convert_text_to_speech(self, text: str, config: TTSConfig, retries: int = 3) -> bytes:
        """Convert text to speech with retry logic."""
        for attempt in range(retries):
            try:
                response = await self.session.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": config.model,
                        "voice": config.voice,
                        "response_format": config.response_format,
                        "speed": config.speed,
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
                    await asyncio.sleep(2 ** attempt)
                    
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
    
    def split_text_into_chunks(self, text: str, max_chars: int = 4096) -> List[str]:
        """Split text into chunks respecting word boundaries."""
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        while text:
            if len(text) <= max_chars:
                chunks.append(text)
                break
            
            # Find the last space within the limit
            split_point = text.rfind(' ', 0, max_chars)
            if split_point == -1:
                split_point = max_chars
            
            chunks.append(text[:split_point])
            text = text[split_point:].lstrip()
        
        return chunks
    
    async def process_tts_file(self, file_path: str, config: TTSConfig, output_dir: Optional[str] = None) -> bool:
        """Process a text file and convert it to speech."""
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            logger.info(f"Processing TTS file: {file_path}")
            logger.info(f"Text length: {len(text_content)} characters")
            
            # Split into chunks if necessary
            chunks = self.split_text_into_chunks(text_content, config.max_chars)
            logger.info(f"Split into {len(chunks)} chunks")
            
            # Determine output path
            input_path = Path(file_path)
            if output_dir:
                output_path = Path(output_dir) / f"{input_path.stem}.{config.response_format}"
            else:
                output_path = input_path.with_suffix(f'.{config.response_format}')
            
            # Process chunks
            if len(chunks) == 1:
                logger.info("Processing single chunk...")
                audio_data = await self.convert_text_to_speech(chunks[0], config)
                
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                
                logger.info(f"✅ Successfully created: {output_path}")
                logger.info(f"File size: {len(audio_data)} bytes")
                
            else:
                logger.info("Processing multiple chunks...")
                temp_files = []
                
                for i, chunk in enumerate(chunks, 1):
                    logger.info(f"Processing chunk {i}/{len(chunks)}...")
                    
                    audio_data = await self.convert_text_to_speech(chunk, config)
                    
                    # Save temporary file
                    temp_path = output_path.with_stem(f"{output_path.stem}_temp_{i}")
                    with open(temp_path, 'wb') as f:
                        f.write(audio_data)
                    temp_files.append(temp_path)
                    
                    logger.info(f"✅ Chunk {i} saved: {temp_path}")
                    
                    # Rate limiting (except for last chunk)
                    if i < len(chunks):
                        delay = 6 if config.model == "tts-1-hd" else 0.6
                        logger.info(f"⏳ Waiting {delay}s for rate limit...")
                        await asyncio.sleep(delay)
                
                logger.info(f"✅ All chunks processed. Individual files saved:")
                for temp_file in temp_files:
                    logger.info(f"  - {temp_file}")
                logger.info("Note: Use a media player to combine the files if needed.")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing TTS file: {e}")
            return False
    
    # Transcription Methods
    async def upload_file_for_transcription(self, file_path: str) -> str:
        """Upload a file for batch transcription."""
        try:
            logger.info(f"Uploading file for transcription: {file_path}")
            
            # Prepare the file for upload
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'audio/*')}
                
                response = await self.session.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data={
                        "model": "whisper-1",
                        "response_format": "verbose_json",
                        "language": "en"
                    },
                    files=files,
                    timeout=aiohttp.ClientTimeout(total=300)  # 5 minutes for upload
                )
            
            if response.status == 200:
                result = await response.json()
                logger.info("✅ File uploaded successfully for transcription")
                return result
            else:
                error_text = await response.text()
                logger.error(f"Upload failed: {response.status} - {error_text}")
                raise Exception(f"Upload failed: {response.status}")
                
        except Exception as e:
            logger.error(f"❌ Error uploading file: {e}")
            raise
    
    async def check_transcription_status(self, task_id: str) -> Dict:
        """Check the status of a batch transcription task."""
        try:
            response = await self.session.get(
                f"https://api.openai.com/v1/audio/transcriptions/{task_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                logger.error(f"Status check failed: {response.status} - {error_text}")
                raise Exception(f"Status check failed: {response.status}")
                
        except Exception as e:
            logger.error(f"❌ Error checking status: {e}")
            raise
    
    async def process_transcription_file(self, file_path: str, config: TranscriptionConfig, output_dir: Optional[str] = None) -> bool:
        """Process an audio file for transcription."""
        try:
            logger.info(f"Processing transcription file: {file_path}")
            
            # Upload file for transcription
            result = await self.upload_file_for_transcription(file_path)
            
            # Determine output path
            input_path = Path(file_path)
            if output_dir:
                output_path = Path(output_dir) / f"{input_path.stem}_transcription.json"
            else:
                output_path = input_path.with_suffix('_transcription.json')
            
            # Save transcription result
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"✅ Transcription completed: {output_path}")
            
            # Extract and save plain text if available
            if 'text' in result:
                text_output_path = output_path.with_suffix('.txt')
                with open(text_output_path, 'w') as f:
                    f.write(result['text'])
                logger.info(f"✅ Text extracted: {text_output_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing transcription file: {e}")
            return False

class UserInterface:
    """Unified user interface for audio processing."""
    
    def __init__(self):
        self.tts_config = TTSConfig()
        self.transcription_config = TranscriptionConfig()
    
    def get_api_key(self) -> Optional[str]:
        """Get API key from environment or user input."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Please set your OpenAI API key:")
            print("1. Set environment variable: export OPENAI_API_KEY='your-key-here'")
            print("2. Or enter it when prompted")
            api_key = input("Enter your OpenAI API key: ").strip()
        
        return api_key if api_key else None
    
    def select_processing_mode(self) -> str:
        """Let user select the processing mode."""
        print("\n🎤 OpenAI Audio Processing Tool")
        print("=" * 40)
        print("Available processing modes:")
        print("1. Text-to-Speech (Real-time)")
        print("2. Audio Transcription (Batch)")
        
        while True:
            choice = input("Select mode (1 or 2): ").strip()
            if choice == "1":
                return "tts"
            elif choice == "2":
                return "transcription"
            else:
                print("Please enter 1 or 2.")
    
    def configure_tts_settings(self):
        """Configure TTS settings."""
        print("\n" + "="*30)
        print("CONFIGURE TTS SETTINGS")
        print("="*30)
        
        # Model selection
        print("\nAvailable models:")
        print("1. tts-1 (Normal) - Faster, lower quality")
        print("2. tts-1-hd (High Definition) - Slower, higher quality")
        
        while True:
            choice = input("Select model (1 or 2): ").strip()
            if choice == "1":
                self.tts_config.model = "tts-1"
                self.tts_config.rate_limit_delay = 0.6
                break
            elif choice == "2":
                self.tts_config.model = "tts-1-hd"
                self.tts_config.rate_limit_delay = 6
                break
            else:
                print("Please enter 1 or 2.")
        
        # Voice selection
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
                self.tts_config.voice = voices[choice]
                break
            else:
                print("Please enter a number between 1 and 6.")
        
        # Speed selection
        print("\nSpeech speed:")
        print("1. Slow (0.75x)")
        print("2. Normal (1.0x)")
        print("3. Fast (1.25x)")
        print("4. Very Fast (1.5x)")
        
        speeds = {"1": 0.75, "2": 1.0, "3": 1.25, "4": 1.5}
        
        while True:
            choice = input("Select speed (1-4): ").strip()
            if choice in speeds:
                self.tts_config.speed = speeds[choice]
                break
            else:
                print("Please enter a number between 1 and 4.")
    
    def configure_transcription_settings(self):
        """Configure transcription settings."""
        print("\n" + "="*30)
        print("CONFIGURE TRANSCRIPTION SETTINGS")
        print("="*30)
        
        # Language selection
        print("\nLanguage options:")
        print("1. Auto-detect (recommended)")
        print("2. English")
        print("3. Spanish")
        print("4. French")
        print("5. German")
        
        languages = {
            "1": None,
            "2": "en",
            "3": "es", 
            "4": "fr",
            "5": "de"
        }
        
        while True:
            choice = input("Select language (1-5): ").strip()
            if choice in languages:
                self.transcription_config.language = languages[choice]
                break
            else:
                print("Please enter a number between 1 and 5.")
        
        # Optional prompt
        print("\nOptional prompt (to help with context):")
        prompt = input("Enter prompt (or press Enter to skip): ").strip()
        if prompt:
            self.transcription_config.prompt = prompt
    
    def get_file_path(self, mode: str) -> Optional[str]:
        """Get the input file path."""
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            if os.path.exists(file_path):
                return file_path
            else:
                print(f"Error: File '{file_path}' not found.")
                return None
        
        if mode == "tts":
            print("\nEnter the path to your text file:")
        else:
            print("\nEnter the path to your audio file:")
            print("Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm")
        
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
    interface = UserInterface()
    
    # Get API key
    api_key = interface.get_api_key()
    if not api_key:
        print("❌ API key is required.")
        return
    
    # Select processing mode
    mode = interface.select_processing_mode()
    
    # Configure settings based on mode
    if mode == "tts":
        interface.configure_tts_settings()
    else:
        interface.configure_transcription_settings()
    
    # Get file path
    file_path = interface.get_file_path(mode)
    if not file_path:
        print("❌ No valid file selected.")
        return
    
    # Get output directory
    output_dir = interface.get_output_directory()
    
    # Process the file
    async with AudioProcessor(api_key) as processor:
        if mode == "tts":
            success = await processor.process_tts_file(file_path, interface.tts_config, output_dir)
        else:
            success = await processor.process_transcription_file(file_path, interface.transcription_config, output_dir)
        
        if success:
            print("\n🎉 Processing completed successfully!")
            print(f"Check the log file 'audio_processor.log' for details.")
        else:
            print("\n💥 Processing failed. Check the log file for details.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        print("Check the log file for more details.")