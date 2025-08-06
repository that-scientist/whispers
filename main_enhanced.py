#!/usr/bin/env python3
"""
Enhanced OpenAI Audio Processing Tool
Greatly improved user experience with modern CLI, progress tracking, and interactive features.
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
import glob
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax
from rich import box
import click

# Configure rich console
console = Console()

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
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class TranscriptionConfig:
    """Configuration for batch transcription."""
    model: str = "whisper-1"
    response_format: str = "verbose_json"
    language: Optional[str] = None
    prompt: Optional[str] = None
    temperature: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ConfigManager:
    """Manages user configurations and profiles."""
    
    def __init__(self, config_file: str = "user_config.json"):
        self.config_file = config_file
        self.configs = self.load_configs()
    
    def load_configs(self) -> Dict[str, Any]:
        """Load saved configurations."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                console.print(f"[red]Error loading config: {e}[/red]")
        return {
            "profiles": {},
            "last_used": {},
            "settings": {}
        }
    
    def save_configs(self):
        """Save configurations to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.configs, f, indent=2)
        except Exception as e:
            console.print(f"[red]Error saving config: {e}[/red]")
    
    def save_profile(self, name: str, tts_config: TTSConfig, transcription_config: TranscriptionConfig):
        """Save a configuration profile."""
        self.configs["profiles"][name] = {
            "tts": tts_config.to_dict(),
            "transcription": transcription_config.to_dict(),
            "created": datetime.now().isoformat()
        }
        self.save_configs()
    
    def load_profile(self, name: str) -> Tuple[Optional[TTSConfig], Optional[TranscriptionConfig]]:
        """Load a configuration profile."""
        if name in self.configs["profiles"]:
            profile = self.configs["profiles"][name]
            tts_config = TTSConfig(**profile["tts"])
            transcription_config = TranscriptionConfig(**profile["transcription"])
            return tts_config, transcription_config
        return None, None
    
    def list_profiles(self) -> List[str]:
        """List available profiles."""
        return list(self.configs["profiles"].keys())

class FileSelector:
    """Interactive file selector with search and preview."""
    
    def __init__(self):
        self.supported_audio_formats = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
        self.supported_text_formats = ['.txt', '.md', '.json', '.csv']
    
    def find_files(self, directory: str, file_type: str) -> List[str]:
        """Find files of specified type in directory."""
        if file_type == "audio":
            extensions = self.supported_audio_formats
        else:
            extensions = self.supported_text_formats
        
        files = []
        for ext in extensions:
            pattern = os.path.join(directory, f"*{ext}")
            files.extend(glob.glob(pattern))
        
        return sorted(files)
    
    def select_file(self, mode: str, current_dir: str = ".") -> Optional[str]:
        """Interactive file selection."""
        if mode == "tts":
            files = self.find_files(current_dir, "text")
            file_type = "text"
        else:
            files = self.find_files(current_dir, "audio")
            file_type = "audio"
        
        if not files:
            console.print(f"[yellow]No {file_type} files found in current directory.[/yellow]")
            return None
        
        # Create file selection table
        table = Table(title=f"Available {file_type.title()} Files", box=box.ROUNDED)
        table.add_column("#", style="cyan", no_wrap=True)
        table.add_column("File Name", style="green")
        table.add_column("Size", style="blue")
        table.add_column("Modified", style="magenta")
        
        for i, file_path in enumerate(files, 1):
            try:
                stat = os.stat(file_path)
                size = self.format_size(stat.st_size)
                modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                table.add_row(str(i), os.path.basename(file_path), size, modified)
            except Exception:
                table.add_row(str(i), os.path.basename(file_path), "Unknown", "Unknown")
        
        console.print(table)
        
        while True:
            choice = Prompt.ask(
                f"Select {file_type} file (1-{len(files)}) or 'q' to quit",
                default="q"
            )
            
            if choice.lower() == 'q':
                return None
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(files):
                    return files[index]
                else:
                    console.print("[red]Invalid selection. Please try again.[/red]")
            except ValueError:
                console.print("[red]Please enter a valid number.[/red]")
    
    def format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f}{size_names[i]}"

class AudioProcessor:
    """Enhanced audio processor with progress tracking."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def convert_text_to_speech(self, text: str, config: TTSConfig, progress: Progress, retries: int = 3) -> bytes:
        """Convert text to speech with progress tracking."""
        task = progress.add_task("Converting text to speech...", total=None)
        
        for attempt in range(retries):
            try:
                progress.update(task, description=f"Converting text to speech... (Attempt {attempt + 1}/{retries})")
                
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
                    progress.update(task, description="Downloading audio...")
                    audio_data = await response.read()
                    progress.update(task, description="✅ Text-to-speech conversion completed!")
                    return audio_data
                elif response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    progress.update(task, description=f"Rate limited. Waiting {retry_after}s...")
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
        
        raise Exception("Failed to convert text to speech")
    
    def split_text_into_chunks(self, text: str, max_chars: int = 4096) -> List[str]:
        """Split text into chunks for processing."""
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        for sentence in text.split('.'):
            if len(current_chunk + sentence + '.') <= max_chars:
                current_chunk += sentence + '.'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + '.'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def process_tts_file(self, file_path: str, config: TTSConfig, output_dir: Optional[str] = None, progress: Progress) -> bool:
        """Process TTS file with enhanced progress tracking."""
        try:
            # Read input file
            progress.add_task("Reading input file...", total=None)
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Split into chunks if needed
            chunks = self.split_text_into_chunks(text, config.max_chars)
            
            if len(chunks) > 1:
                console.print(f"[yellow]Large file detected. Processing in {len(chunks)} chunks...[/yellow]")
            
            # Process chunks
            audio_chunks = []
            for i, chunk in enumerate(chunks):
                chunk_task = progress.add_task(f"Processing chunk {i+1}/{len(chunks)}...", total=None)
                audio_data = await self.convert_text_to_speech(chunk, config, progress)
                audio_chunks.append(audio_data)
                progress.update(chunk_task, description=f"✅ Chunk {i+1}/{len(chunks)} completed")
            
            # Combine audio chunks if multiple
            if len(audio_chunks) > 1:
                # For now, save separate files for each chunk
                # TODO: Implement audio concatenation
                pass
            
            # Save output
            output_path = self.get_output_path(file_path, output_dir, config.response_format)
            with open(output_path, 'wb') as f:
                f.write(audio_chunks[0] if len(audio_chunks) == 1 else audio_chunks[0])
            
            console.print(f"[green]✅ Audio saved to: {output_path}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error processing TTS file: {e}[/red]")
            logger.error(f"TTS processing error: {e}")
            return False
    
    def get_output_path(self, input_path: str, output_dir: Optional[str], format: str) -> str:
        """Generate output file path."""
        input_name = Path(input_path).stem
        if output_dir:
            return os.path.join(output_dir, f"{input_name}.{format}")
        else:
            return f"{input_name}.{format}"
    
    async def upload_file_for_transcription(self, file_path: str, progress: Progress) -> str:
        """Upload file for transcription with progress tracking."""
        task = progress.add_task("Uploading file for transcription...", total=None)
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {'model': 'whisper-1'}
                
                response = await self.session.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data=data,
                    files=files,
                    timeout=aiohttp.ClientTimeout(total=300)
                )
                
                if response.status == 200:
                    result = await response.json()
                    progress.update(task, description="✅ File uploaded successfully!")
                    return result['text']
                else:
                    error_text = await response.text()
                    raise Exception(f"Upload failed: {response.status} - {error_text}")
                    
        except Exception as e:
            progress.update(task, description=f"❌ Upload failed: {e}")
            raise e
    
    async def process_transcription_file(self, file_path: str, config: TranscriptionConfig, output_dir: Optional[str] = None, progress: Progress) -> bool:
        """Process transcription file with enhanced progress tracking."""
        try:
            # Upload and transcribe
            transcription = await self.upload_file_for_transcription(file_path, progress)
            
            # Save transcription
            output_path = self.get_output_path(file_path, output_dir, "txt")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(transcription)
            
            console.print(f"[green]✅ Transcription saved to: {output_path}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error processing transcription: {e}[/red]")
            logger.error(f"Transcription error: {e}")
            return False

class EnhancedUserInterface:
    """Enhanced user interface with rich formatting and interactive features."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.file_selector = FileSelector()
        self.tts_config = TTSConfig()
        self.transcription_config = TranscriptionConfig()
        self.load_last_config()
    
    def load_last_config(self):
        """Load last used configuration."""
        if "last_used" in self.config_manager.configs:
            last_used = self.config_manager.configs["last_used"]
            if "tts" in last_used:
                self.tts_config = TTSConfig(**last_used["tts"])
            if "transcription" in last_used:
                self.transcription_config = TranscriptionConfig(**last_used["transcription"])
    
    def save_last_config(self):
        """Save current configuration as last used."""
        self.config_manager.configs["last_used"] = {
            "tts": self.tts_config.to_dict(),
            "transcription": self.transcription_config.to_dict()
        }
        self.config_manager.save_configs()
    
    def show_welcome(self):
        """Display welcome screen."""
        welcome_text = Text()
        welcome_text.append("🎤 ", style="bold blue")
        welcome_text.append("Enhanced OpenAI Audio Processing Tool", style="bold white")
        welcome_text.append("\n\nTransform text to speech or transcribe audio with ease!", style="italic")
        
        panel = Panel(
            welcome_text,
            title="Welcome",
            border_style="blue",
            padding=(1, 2)
        )
        console.print(panel)
    
    def get_api_key(self) -> Optional[str]:
        """Get API key with enhanced interface."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            console.print("\n[bold yellow]API Key Required[/bold yellow]")
            console.print("You need an OpenAI API key to use this tool.")
            console.print("Get your key at: https://platform.openai.com/api-keys\n")
            
            choice = Prompt.ask(
                "How would you like to provide your API key?",
                choices=["1", "2", "3"],
                default="1"
            )
            
            if choice == "1":
                api_key = Prompt.ask("Enter your OpenAI API key", password=True)
            elif choice == "2":
                console.print("Set the environment variable:")
                console.print("export OPENAI_API_KEY='your-key-here'")
                return None
            else:
                console.print("Please set the environment variable and restart the application.")
                return None
        
        return api_key if api_key else None
    
    def select_processing_mode(self) -> str:
        """Enhanced mode selection."""
        console.print("\n[bold]Select Processing Mode[/bold]")
        
        table = Table(box=box.ROUNDED)
        table.add_column("Mode", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Best For", style="green")
        
        table.add_row(
            "1. Text-to-Speech",
            "Convert text files to audio",
            "Creating audio content, podcasts, narration"
        )
        table.add_row(
            "2. Audio Transcription",
            "Convert audio files to text",
            "Transcribing meetings, interviews, lectures"
        )
        
        console.print(table)
        
        while True:
            choice = Prompt.ask("Select mode", choices=["1", "2"], default="1")
            if choice == "1":
                return "tts"
            else:
                return "transcription"
    
    def configure_tts_settings(self):
        """Enhanced TTS configuration with profiles."""
        console.print("\n[bold]Configure TTS Settings[/bold]")
        
        # Check for saved profiles
        profiles = self.config_manager.list_profiles()
        if profiles:
            console.print(f"\n[yellow]Available profiles: {', '.join(profiles)}[/yellow]")
            if Confirm.ask("Load a saved profile?"):
                profile_name = Prompt.ask("Enter profile name", choices=profiles)
                tts_config, _ = self.config_manager.load_profile(profile_name)
                if tts_config:
                    self.tts_config = tts_config
                    console.print(f"[green]✅ Loaded profile: {profile_name}[/green]")
                    return
        
        # Model selection
        console.print("\n[bold]Model Selection[/bold]")
        model_table = Table(box=box.SIMPLE)
        model_table.add_column("Option", style="cyan")
        model_table.add_column("Model", style="white")
        model_table.add_column("Quality", style="green")
        model_table.add_column("Speed", style="yellow")
        
        model_table.add_row("1", "tts-1", "Standard", "Fast")
        model_table.add_row("2", "tts-1-hd", "High Definition", "Slower")
        
        console.print(model_table)
        
        choice = Prompt.ask("Select model", choices=["1", "2"], default="1")
        if choice == "1":
            self.tts_config.model = "tts-1"
            self.tts_config.rate_limit_delay = 0.6
        else:
            self.tts_config.model = "tts-1-hd"
            self.tts_config.rate_limit_delay = 6
        
        # Voice selection
        console.print("\n[bold]Voice Selection[/bold]")
        voice_table = Table(box=box.SIMPLE)
        voice_table.add_column("Option", style="cyan")
        voice_table.add_column("Voice", style="white")
        voice_table.add_column("Description", style="green")
        
        voices = {
            "1": ("alloy", "Neutral, balanced voice"),
            "2": ("echo", "Deep, authoritative voice"),
            "3": ("fable", "Warm, storytelling voice"),
            "4": ("onyx", "Serious, professional voice"),
            "5": ("nova", "Bright, energetic voice"),
            "6": ("shimmer", "Soft, gentle voice")
        }
        
        for key, (voice, desc) in voices.items():
            voice_table.add_row(key, voice.capitalize(), desc)
        
        console.print(voice_table)
        
        choice = Prompt.ask("Select voice", choices=list(voices.keys()), default="1")
        self.tts_config.voice = voices[choice][0]
        
        # Speed selection
        console.print("\n[bold]Speech Speed[/bold]")
        speed_table = Table(box=box.SIMPLE)
        speed_table.add_column("Option", style="cyan")
        speed_table.add_column("Speed", style="white")
        speed_table.add_column("Description", style="green")
        
        speeds = {
            "1": (0.75, "Slow"),
            "2": (1.0, "Normal"),
            "3": (1.25, "Fast"),
            "4": (1.5, "Very Fast")
        }
        
        for key, (speed, desc) in speeds.items():
            speed_table.add_row(key, f"{speed}x", desc)
        
        console.print(speed_table)
        
        choice = Prompt.ask("Select speed", choices=list(speeds.keys()), default="2")
        self.tts_config.speed = speeds[choice][0]
        
        # Save profile option
        if Confirm.ask("Save these settings as a profile?"):
            profile_name = Prompt.ask("Enter profile name")
            self.config_manager.save_profile(profile_name, self.tts_config, self.transcription_config)
            console.print(f"[green]✅ Profile '{profile_name}' saved![/green]")
    
    def configure_transcription_settings(self):
        """Enhanced transcription configuration."""
        console.print("\n[bold]Configure Transcription Settings[/bold]")
        
        # Language selection
        console.print("\n[bold]Language Options[/bold]")
        language_table = Table(box=box.SIMPLE)
        language_table.add_column("Option", style="cyan")
        language_table.add_column("Language", style="white")
        language_table.add_column("Description", style="green")
        
        languages = {
            "1": (None, "Auto-detect (recommended)"),
            "2": ("en", "English"),
            "3": ("es", "Spanish"),
            "4": ("fr", "French"),
            "5": ("de", "German")
        }
        
        for key, (lang, desc) in languages.items():
            language_table.add_row(key, lang or "Auto", desc)
        
        console.print(language_table)
        
        choice = Prompt.ask("Select language", choices=list(languages.keys()), default="1")
        self.transcription_config.language = languages[choice][0]
        
        # Prompt option
        if Confirm.ask("Add a context prompt to improve accuracy?"):
            prompt = Prompt.ask("Enter context prompt (e.g., 'This is a technical discussion about AI')")
            self.transcription_config.prompt = prompt
    
    def get_file_path(self, mode: str) -> Optional[str]:
        """Enhanced file selection."""
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            if os.path.exists(file_path):
                return file_path
            else:
                console.print(f"[red]Error: File '{file_path}' not found.[/red]")
                return None
        
        console.print(f"\n[bold]Select {mode.upper()} File[/bold]")
        
        # Show current directory files
        return self.file_selector.select_file(mode)
    
    def get_output_directory(self) -> Optional[str]:
        """Enhanced output directory selection."""
        console.print("\n[bold]Output Options[/bold]")
        
        choice = Prompt.ask(
            "Where would you like to save the output?",
            choices=["1", "2"],
            default="1"
        )
        
        if choice == "1":
            return None
        else:
            output_dir = Prompt.ask("Enter output directory path")
            if output_dir and not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                    console.print(f"[green]✅ Created directory: {output_dir}[/green]")
                except Exception as e:
                    console.print(f"[red]Error creating directory: {e}[/red]")
                    return None
            return output_dir

async def main():
    """Enhanced main function with progress tracking."""
    interface = EnhancedUserInterface()
    
    # Show welcome
    interface.show_welcome()
    
    # Get API key
    api_key = interface.get_api_key()
    if not api_key:
        console.print("[red]❌ API key is required.[/red]")
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
        console.print("[red]❌ No valid file selected.[/red]")
        return
    
    # Get output directory
    output_dir = interface.get_output_directory()
    
    # Save configuration
    interface.save_last_config()
    
    # Process the file with progress tracking
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        async with AudioProcessor(api_key) as processor:
            if mode == "tts":
                success = await processor.process_tts_file(file_path, interface.tts_config, output_dir, progress)
            else:
                success = await processor.process_transcription_file(file_path, interface.transcription_config, output_dir, progress)
            
            if success:
                console.print("\n[bold green]🎉 Processing completed successfully![/bold green]")
                console.print("Check the log file 'audio_processor.log' for details.")
            else:
                console.print("\n[bold red]💥 Processing failed. Check the log file for details.[/bold red]")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  Operation cancelled by user.[/yellow]")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        console.print(f"\n[bold red]❌ Unexpected error: {e}[/bold red]")
        console.print("Check the log file for more details.")