#!/usr/bin/env python3
"""
Enhanced Batch TTS Converter
Process multiple text files with consistent settings and better error handling.
"""

import os
import asyncio
import aiohttp
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
import glob
import sys

# Import the enhanced converter
from app_enhanced import TTSConverter, TTSConfig, TTSInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_tts_converter.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BatchTTSProcessor:
    """Batch processor for multiple text files."""
    
    def __init__(self, api_key: str, config: TTSConfig):
        self.api_key = api_key
        self.config = config
        self.results: List[Dict] = []
    
    async def process_directory(self, input_dir: str, output_dir: Optional[str] = None) -> bool:
        """Process all text files in a directory."""
        try:
            # Find all text files
            text_files = []
            for ext in ['*.txt', '*.md', '*.text']:
                text_files.extend(glob.glob(os.path.join(input_dir, ext)))
            
            if not text_files:
                logger.warning(f"No text files found in {input_dir}")
                return False
            
            logger.info(f"Found {len(text_files)} text files to process")
            
            # Create output directory if specified
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Process each file
            async with TTSConverter(self.api_key, self.config) as converter:
                for i, file_path in enumerate(text_files, 1):
                    logger.info(f"Processing file {i}/{len(text_files)}: {file_path}")
                    
                    try:
                        success = await converter.process_file(file_path, output_dir)
                        
                        result = {
                            'file': file_path,
                            'success': success,
                            'timestamp': asyncio.get_event_loop().time()
                        }
                        
                        if success:
                            logger.info(f"✅ Successfully processed: {file_path}")
                        else:
                            logger.error(f"❌ Failed to process: {file_path}")
                        
                        self.results.append(result)
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing {file_path}: {e}")
                        self.results.append({
                            'file': file_path,
                            'success': False,
                            'error': str(e),
                            'timestamp': asyncio.get_event_loop().time()
                        })
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in batch processing: {e}")
            return False
    
    async def process_file_list(self, file_list: List[str], output_dir: Optional[str] = None) -> bool:
        """Process a specific list of files."""
        try:
            logger.info(f"Processing {len(file_list)} files")
            
            # Create output directory if specified
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Process each file
            async with TTSConverter(self.api_key, self.config) as converter:
                for i, file_path in enumerate(file_list, 1):
                    logger.info(f"Processing file {i}/{len(file_list)}: {file_path}")
                    
                    if not os.path.exists(file_path):
                        logger.error(f"❌ File not found: {file_path}")
                        self.results.append({
                            'file': file_path,
                            'success': False,
                            'error': 'File not found',
                            'timestamp': asyncio.get_event_loop().time()
                        })
                        continue
                    
                    try:
                        success = await converter.process_file(file_path, output_dir)
                        
                        result = {
                            'file': file_path,
                            'success': success,
                            'timestamp': asyncio.get_event_loop().time()
                        }
                        
                        if success:
                            logger.info(f"✅ Successfully processed: {file_path}")
                        else:
                            logger.error(f"❌ Failed to process: {file_path}")
                        
                        self.results.append(result)
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing {file_path}: {e}")
                        self.results.append({
                            'file': file_path,
                            'success': False,
                            'error': str(e),
                            'timestamp': asyncio.get_event_loop().time()
                        })
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in batch processing: {e}")
            return False
    
    def print_summary(self):
        """Print a summary of the batch processing results."""
        total_files = len(self.results)
        successful_files = sum(1 for r in self.results if r.get('success', False))
        failed_files = total_files - successful_files
        
        print("\n" + "="*50)
        print("📊 BATCH PROCESSING SUMMARY")
        print("="*50)
        print(f"Total files processed: {total_files}")
        print(f"✅ Successful: {successful_files}")
        print(f"❌ Failed: {failed_files}")
        print(f"Success rate: {(successful_files/total_files)*100:.1f}%" if total_files > 0 else "N/A")
        
        if failed_files > 0:
            print("\n❌ Failed files:")
            for result in self.results:
                if not result.get('success', False):
                    error = result.get('error', 'Unknown error')
                    print(f"  - {result['file']}: {error}")
        
        print("\n✅ Successful files:")
        for result in self.results:
            if result.get('success', False):
                print(f"  - {result['file']}")

class BatchTTSInterface:
    """User interface for batch TTS processing."""
    
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
    
    def select_processing_mode(self) -> str:
        """Let user select the processing mode."""
        print("\nBatch processing modes:")
        print("1. Process all text files in a directory")
        print("2. Process specific files from a list")
        
        while True:
            choice = input("Select mode (1 or 2): ").strip()
            if choice in ["1", "2"]:
                return choice
            else:
                print("Please enter 1 or 2.")
    
    def get_input_directory(self) -> Optional[str]:
        """Get the input directory for batch processing."""
        print("\nEnter the directory containing text files:")
        directory = input("Directory path: ").strip()
        
        if not directory:
            return None
        
        if not os.path.exists(directory):
            print(f"Error: Directory '{directory}' not found.")
            return None
        
        if not os.path.isdir(directory):
            print(f"Error: '{directory}' is not a directory.")
            return None
        
        return directory
    
    def get_file_list(self) -> List[str]:
        """Get a list of files to process."""
        print("\nEnter file paths (one per line, empty line to finish):")
        file_list = []
        
        while True:
            file_path = input("File path: ").strip()
            if not file_path:
                break
            
            if os.path.exists(file_path):
                file_list.append(file_path)
            else:
                print(f"Warning: File '{file_path}' not found, skipping.")
        
        return file_list
    
    def get_output_directory(self) -> Optional[str]:
        """Get the output directory."""
        print("\nOutput options:")
        print("1. Save in same directory as each input file")
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
    
    def configure_settings(self):
        """Configure TTS settings."""
        # Import the interface from the enhanced app
        interface = TTSInterface()
        
        print("\n" + "="*30)
        print("CONFIGURE TTS SETTINGS")
        print("="*30)
        
        interface.select_model()
        interface.select_voice()
        interface.select_speed()
        
        # Copy settings to our config
        self.config = interface.config

async def main():
    """Main function for batch processing."""
    print("🎤 Enhanced Batch TTS Converter")
    print("=" * 50)
    
    interface = BatchTTSInterface()
    
    # Get API key
    api_key = interface.get_api_key()
    if not api_key:
        print("❌ API key is required.")
        return
    
    # Configure settings
    interface.configure_settings()
    
    # Get processing mode
    mode = interface.select_processing_mode()
    
    # Get input and output
    if mode == "1":
        input_dir = interface.get_input_directory()
        if not input_dir:
            print("❌ No valid directory selected.")
            return
    else:
        file_list = interface.get_file_list()
        if not file_list:
            print("❌ No files selected.")
            return
    
    # Get output directory
    output_dir = interface.get_output_directory()
    
    # Process files
    processor = BatchTTSProcessor(api_key, interface.config)
    
    if mode == "1":
        success = await processor.process_directory(input_dir, output_dir)
    else:
        success = await processor.process_file_list(file_list, output_dir)
    
    # Print summary
    processor.print_summary()
    
    if success:
        print("\n🎉 Batch processing completed!")
        print(f"Check the log file 'batch_tts_converter.log' for details.")
    else:
        print("\n💥 Batch processing failed. Check the log file for details.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        print("Check the log file for more details.")