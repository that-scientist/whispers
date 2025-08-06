#!/usr/bin/env python3
"""
Unified OpenAI Audio Processing Tool

This module provides a comprehensive interface for both Text-to-Speech (TTS) and 
Audio Transcription using OpenAI's APIs. All operations use file upload for 
reliability and to handle large files efficiently.

Key Features:
- TTS: Convert text files to speech using file upload
- Transcription: Convert audio files to text using file upload
- Text Cleaning: Advanced text preprocessing using large LLMs
- Rate limiting: Automatic handling of API rate limits
- Error recovery: Robust retry logic with exponential backoff
- Logging: Comprehensive logging for debugging and monitoring

Author: OpenAI Audio Processing Team
Version: 2.1.0
"""

import os
import asyncio
import aiohttp
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import sys
import time

# Import text cleaning functionality
try:
    from text_cleaner import TextCleaner, TextCleaningConfig, CleaningResult
    TEXT_CLEANING_AVAILABLE = True
except ImportError:
    TEXT_CLEANING_AVAILABLE = False
    print("Warning: Text cleaning module not available. Install with: pip install openai")

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('audio_processor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TTSConfig:
    """
    Configuration for Text-to-Speech conversion.
    
    Attributes:
        model: OpenAI TTS model to use ('tts-1' or 'tts-1-hd')
        voice: Voice identifier for speech synthesis
        response_format: Audio output format ('aac', 'mp3', 'opus', 'flac')
        speed: Speech rate multiplier (0.75 to 1.5)
        max_chars: Maximum characters per request (for chunking if needed)
        rate_limit_delay: Delay between requests to respect rate limits
        enable_text_cleaning: Whether to clean text before TTS processing
        cleaning_config: Configuration for text cleaning if enabled
    """
    model: str = "tts-1"
    voice: str = "alloy"
    response_format: str = "aac"
    speed: float = 1.1
    max_chars: int = 4096
    rate_limit_delay: float = 0.6
    enable_text_cleaning: bool = False
    cleaning_config: Optional[TextCleaningConfig] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return asdict(self)

@dataclass
class TranscriptionConfig:
    """
    Configuration for audio transcription.
    
    Attributes:
        model: OpenAI Whisper model to use (typically 'whisper-1')
        response_format: Output format ('json', 'verbose_json', 'text', 'srt', 'vtt')
        language: Language code for transcription (None for auto-detect)
        prompt: Context prompt to improve transcription accuracy
        temperature: Sampling temperature (0.0 for deterministic output)
    """
    model: str = "whisper-1"
    response_format: str = "verbose_json"
    language: Optional[str] = None
    prompt: Optional[str] = None
    temperature: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return asdict(self)

class AudioProcessor:
    """
    Unified audio processor for TTS and transcription using file upload.
    
    This class handles all interactions with OpenAI's audio APIs, including
    file uploads, rate limiting, error handling, and response processing.
    Now includes optional text cleaning capabilities for improved TTS quality.
    
    Attributes:
        api_key: OpenAI API key for authentication
        session: aiohttp client session for HTTP requests
        text_cleaner: Optional text cleaner for preprocessing
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the audio processor.
        
        Args:
            api_key: Valid OpenAI API key for authentication
        """
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.text_cleaner: Optional[TextCleaner] = None
        
    async def __aenter__(self):
        """Async context manager entry - create HTTP session."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup HTTP session."""
        if self.session:
            await self.session.close()
    
    def _setup_text_cleaner(self, config: TextCleaningConfig):
        """
        Setup text cleaner if text cleaning is enabled.
        
        Args:
            config: Text cleaning configuration
        """
        if TEXT_CLEANING_AVAILABLE and config:
            self.text_cleaner = TextCleaner(self.api_key, config)
        else:
            self.text_cleaner = None
    
    async def _clean_text_if_enabled(self, text: str, config: TTSConfig) -> Tuple[str, Optional[CleaningResult]]:
        """
        Clean text if text cleaning is enabled.
        
        Args:
            text: Text to potentially clean
            config: TTS configuration with cleaning settings
            
        Returns:
            Tuple[str, Optional[CleaningResult]]: Cleaned text and cleaning result
        """
        if not config.enable_text_cleaning or not self.text_cleaner:
            return text, None
        
        try:
            logger.info("🧹 Cleaning text before TTS processing...")
            result = await self.text_cleaner.clean_text(text)
            
            if result.quality_score > 0.5:  # Only use cleaned text if quality is good
                logger.info(f"✅ Text cleaned successfully (quality: {result.quality_score:.2f})")
                return result.cleaned_text, result
            else:
                logger.warning(f"⚠️ Text cleaning quality too low ({result.quality_score:.2f}), using original text")
                return text, result
                
        except Exception as e:
            logger.error(f"❌ Text cleaning failed: {e}, using original text")
            return text, None
    
    async def upload_text_file_for_tts(self, file_path: str, config: TTSConfig, retries: int = 3) -> bytes:
        """
        Upload text file for TTS conversion using file upload.
        
        This method uploads a text file to OpenAI's TTS API and returns
        the generated audio data. It includes comprehensive error handling
        and retry logic with exponential backoff. Now supports optional
        text cleaning before TTS processing.
        
        Args:
            file_path: Path to the text file to convert
            config: TTS configuration settings
            retries: Number of retry attempts for failed requests
            
        Returns:
            bytes: Audio data in the specified format
            
        Raises:
            Exception: If all retry attempts fail
            FileNotFoundError: If the input file doesn't exist
            aiohttp.ClientError: For network-related errors
        """
        # Read the text file
        with open(file_path, 'r', encoding='utf-8') as f:
            original_text = f.read()
        
        # Clean text if enabled
        cleaned_text, cleaning_result = await self._clean_text_if_enabled(original_text, config)
        
        # Create a temporary file with cleaned text if cleaning was performed
        temp_file_path = None
        if cleaning_result and cleaning_result.cleaned_text != original_text:
            temp_file_path = f"{file_path}_cleaned_temp.txt"
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(cleaning_result.cleaned_text)
            file_path_to_upload = temp_file_path
        else:
            file_path_to_upload = file_path
        
        try:
            for attempt in range(retries):
                try:
                    logger.info(f"Uploading text file for TTS: {file_path_to_upload} (Attempt {attempt + 1}/{retries})")
                    
                    # Prepare the file for upload with proper MIME type
                    with open(file_path_to_upload, 'rb') as f:
                        files = {'file': (os.path.basename(file_path_to_upload), f, 'text/plain')}
                        
                        response = await self.session.post(
                            "https://api.openai.com/v1/audio/speech",
                            headers={"Authorization": f"Bearer {self.api_key}"},
                            data={
                                "model": config.model,
                                "voice": config.voice,
                                "response_format": config.response_format,
                                "speed": config.speed
                            },
                            files=files,
                            timeout=aiohttp.ClientTimeout(total=60)
                        )
                    
                    if response.status == 200:
                        audio_data = await response.read()
                        logger.info("✅ Text file uploaded and converted to speech successfully")
                        return audio_data
                    elif response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        error_text = await response.text()
                        logger.error(f"TTS API request failed: {response.status} - {error_text}")
                        if attempt == retries - 1:
                            raise Exception(f"TTS API request failed after {retries} attempts")
                        await asyncio.sleep(2 ** attempt)
                        
                except asyncio.TimeoutError:
                    logger.error(f"TTS request timeout on attempt {attempt + 1}")
                    if attempt == retries - 1:
                        raise Exception("TTS request timeout after all retries")
                    await asyncio.sleep(2 ** attempt)
                except Exception as e:
                    logger.error(f"TTS request failed on attempt {attempt + 1}: {e}")
                    if attempt == retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)
            
            raise Exception("Failed to convert text file to speech")
            
        finally:
            # Clean up temporary file if created
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.debug(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file: {e}")
    
    async def process_tts_file(self, file_path: str, config: TTSConfig, output_dir: Optional[str] = None) -> bool:
        """
        Process a text file and convert it to speech using file upload.
        
        This method handles the complete TTS workflow: file validation,
        optional text cleaning, upload to OpenAI API, and saving the resulting audio file.
        
        Args:
            file_path: Path to the input text file
            config: TTS configuration settings
            output_dir: Optional output directory (uses input directory if None)
            
        Returns:
            bool: True if processing succeeded, False otherwise
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            PermissionError: If output directory is not writable
        """
        try:
            logger.info(f"Processing TTS file: {file_path}")
            
            # Validate input file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Input file not found: {file_path}")
            
            # Setup text cleaner if enabled
            if config.enable_text_cleaning and config.cleaning_config:
                self._setup_text_cleaner(config.cleaning_config)
            
            # Check file size for logging
            file_size = os.path.getsize(file_path)
            logger.info(f"File size: {file_size} bytes")
            
            # Determine output path
            input_path = Path(file_path)
            if output_dir:
                output_path = Path(output_dir) / f"{input_path.stem}.{config.response_format}"
            else:
                output_path = input_path.with_suffix(f'.{config.response_format}')
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Upload file and get audio data
            audio_data = await self.upload_text_file_for_tts(file_path, config)
            
            # Save the audio file
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"✅ Successfully created: {output_path}")
            logger.info(f"Audio file size: {len(audio_data)} bytes")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing TTS file: {e}")
            return False
    
    async def upload_file_for_transcription(self, file_path: str) -> str:
        """
        Upload a file for batch transcription using OpenAI's Whisper API.
        
        This method uploads an audio file to OpenAI's transcription API
        and returns the transcription result as JSON.
        
        Args:
            file_path: Path to the audio file to transcribe
            
        Returns:
            str: JSON string containing transcription data
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            aiohttp.ClientError: For network-related errors
        """
        try:
            logger.info(f"Uploading file for transcription: {file_path}")
            
            # Validate input file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Input file not found: {file_path}")
            
            # Prepare the file for upload with proper MIME type
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
    
    async def process_transcription_file(self, file_path: str, config: TranscriptionConfig, output_dir: Optional[str] = None) -> bool:
        """
        Process an audio file for transcription.
        
        This method handles the complete transcription workflow: file validation,
        upload to OpenAI API, and saving the transcription results.
        
        Args:
            file_path: Path to the input audio file
            config: Transcription configuration settings
            output_dir: Optional output directory (uses input directory if None)
            
        Returns:
            bool: True if processing succeeded, False otherwise
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            PermissionError: If output directory is not writable
        """
        try:
            logger.info(f"Processing transcription file: {file_path}")
            
            # Validate input file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Input file not found: {file_path}")
            
            # Upload file for transcription
            result = await self.upload_file_for_transcription(file_path)
            
            # Determine output path
            input_path = Path(file_path)
            if output_dir:
                output_path = Path(output_dir) / f"{input_path.stem}_transcription.json"
            else:
                output_path = input_path.with_suffix('_transcription.json')
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
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
    """
    Unified user interface for audio processing.
    
    This class handles all user interactions including configuration,
    file selection, and output directory management. Now includes
    text cleaning configuration options.
    
    Attributes:
        tts_config: Current TTS configuration
        transcription_config: Current transcription configuration
    """
    
    def __init__(self):
        """Initialize the user interface with default configurations."""
        self.tts_config = TTSConfig()
        self.transcription_config = TranscriptionConfig()
    
    def get_api_key(self) -> Optional[str]:
        """
        Get API key from environment or user input.
        
        Returns:
            Optional[str]: Valid API key or None if not provided
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Please set your OpenAI API key:")
            print("1. Set environment variable: export OPENAI_API_KEY='your-key-here'")
            print("2. Or enter it when prompted")
            api_key = input("Enter your OpenAI API key: ").strip()
        
        return api_key if api_key else None
    
    def select_processing_mode(self) -> str:
        """
        Let user select the processing mode.
        
        Returns:
            str: Selected mode ('tts' or 'transcription')
        """
        print("\n🎤 OpenAI Audio Processing Tool")
        print("=" * 40)
        print("Available processing modes:")
        print("1. Text-to-Speech (File Upload)")
        print("2. Audio Transcription (File Upload)")
        
        while True:
            choice = input("Select mode (1 or 2): ").strip()
            if choice == "1":
                return "tts"
            elif choice == "2":
                return "transcription"
            else:
                print("Please enter 1 or 2.")
    
    def configure_tts_settings(self):
        """
        Configure TTS settings through interactive prompts.
        
        This method guides users through selecting model, voice, and speed
        options for text-to-speech conversion. Now includes text cleaning options.
        """
        print("\n" + "="*30)
        print("CONFIGURE TTS SETTINGS")
        print("="*30)
        
        # Model selection with clear descriptions
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
        
        # Voice selection with descriptions
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
        
        # Speed selection with clear options
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
        
        # Text cleaning configuration
        if TEXT_CLEANING_AVAILABLE:
            print("\nText Cleaning Options:")
            print("Enable advanced text cleaning using GPT-4 for better TTS quality?")
            enable_cleaning = input("Enable text cleaning? (y/n): ").strip().lower() == 'y'
            
            if enable_cleaning:
                self.tts_config.enable_text_cleaning = True
                self.tts_config.cleaning_config = self._configure_text_cleaning()
                print("✅ Text cleaning enabled")
            else:
                self.tts_config.enable_text_cleaning = False
                print("ℹ️ Text cleaning disabled")
        else:
            print("\nℹ️ Text cleaning not available (requires openai package)")
    
    def _configure_text_cleaning(self) -> TextCleaningConfig:
        """
        Configure text cleaning settings.
        
        Returns:
            TextCleaningConfig: Configured text cleaning settings
        """
        config = TextCleaningConfig()
        
        print("\nText Cleaning Configuration:")
        
        # Model selection
        print("\nAvailable cleaning models:")
        print("1. gpt-4-turbo-preview (Recommended)")
        print("2. gpt-4")
        print("3. gpt-3.5-turbo")
        
        models = {
            "1": "gpt-4-turbo-preview",
            "2": "gpt-4",
            "3": "gpt-3.5-turbo"
        }
        
        while True:
            choice = input("Select cleaning model (1-3): ").strip()
            if choice in models:
                config.model = models[choice]
                break
            else:
                print("Please enter a number between 1 and 3.")
        
        # Cleaning level
        print("\nCleaning level:")
        print("1. Light - Minor corrections only")
        print("2. Medium - Grammar and flow improvements")
        print("3. Aggressive - Major restructuring")
        
        levels = {
            "1": "light",
            "2": "medium",
            "3": "aggressive"
        }
        
        while True:
            choice = input("Select cleaning level (1-3): ").strip()
            if choice in levels:
                config.cleaning_level = levels[choice]
                break
            else:
                print("Please enter a number between 1 and 3.")
        
        # Feature toggles
        config.preserve_formatting = input("Preserve original formatting? (y/n): ").strip().lower() == 'y'
        config.fix_grammar = input("Fix grammar and punctuation? (y/n): ").strip().lower() == 'y'
        config.improve_flow = input("Improve sentence flow? (y/n): ").strip().lower() == 'y'
        
        return config
    
    def configure_transcription_settings(self):
        """
        Configure transcription settings through interactive prompts.
        
        This method guides users through selecting language and prompt
        options for audio transcription.
        """
        print("\n" + "="*30)
        print("CONFIGURE TRANSCRIPTION SETTINGS")
        print("="*30)
        
        # Language selection with clear descriptions
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
        
        # Prompt option for context
        print("\nContext prompt (optional):")
        print("Add a prompt to improve transcription accuracy")
        prompt = input("Enter prompt (or press Enter to skip): ").strip()
        if prompt:
            self.transcription_config.prompt = prompt
    
    def get_file_path(self, mode: str) -> Optional[str]:
        """
        Get the input file path from command line or user input.
        
        Args:
            mode: Processing mode ('tts' or 'transcription')
            
        Returns:
            Optional[str]: Valid file path or None if not provided
        """
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            if os.path.exists(file_path):
                return file_path
            else:
                print(f"Error: File '{file_path}' not found.")
                return None
        
        if mode == "tts":
            print("\nEnter the path to your text file:")
            print("Supported formats: .txt, .md, .json, .csv")
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
        """
        Get the output directory from user input.
        
        Returns:
            Optional[str]: Output directory path or None for same directory
        """
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
    """
    Main function orchestrating the audio processing workflow.
    
    This function handles the complete workflow:
    1. API key validation
    2. Mode selection
    3. Configuration setup
    4. File processing (with optional text cleaning)
    5. Error handling and logging
    """
    interface = UserInterface()
    
    # Get API key with validation
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
    
    # Get file path with validation
    file_path = interface.get_file_path(mode)
    if not file_path:
        print("❌ No valid file selected.")
        return
    
    # Get output directory
    output_dir = interface.get_output_directory()
    
    # Process the file with comprehensive error handling
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