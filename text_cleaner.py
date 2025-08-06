#!/usr/bin/env python3
"""
Text Cleaning Module using Large Language Models

This module provides advanced text cleaning and preprocessing capabilities
using OpenAI's GPT-4.1 and other large language models to improve text
quality before Text-to-Speech conversion.

Key Features:
- Grammar and punctuation correction
- Sentence structure improvement
- Context-aware text enhancement
- Multiple cleaning strategies
- Batch processing support
- Quality scoring and validation

Author: OpenAI Audio Processing Team
Version: 1.0.0
"""

import os
import asyncio
import aiohttp
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import re
import time

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class TextCleaningConfig:
    """
    Configuration for text cleaning operations.
    
    Attributes:
        model: OpenAI model to use for text cleaning ('gpt-4', 'gpt-4-turbo', etc.)
        temperature: Sampling temperature for text generation (0.0 to 2.0)
        max_tokens: Maximum tokens for response generation
        cleaning_level: Level of text cleaning ('light', 'medium', 'aggressive')
        preserve_formatting: Whether to preserve original formatting
        fix_grammar: Whether to fix grammar and punctuation
        improve_flow: Whether to improve sentence flow and structure
        context_prompt: Custom prompt for context-aware cleaning
    """
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.1
    max_tokens: int = 4000
    cleaning_level: str = "medium"
    preserve_formatting: bool = True
    fix_grammar: bool = True
    improve_flow: bool = True
    context_prompt: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return asdict(self)

@dataclass
class CleaningResult:
    """
    Result of text cleaning operation.
    
    Attributes:
        original_text: The original input text
        cleaned_text: The cleaned and improved text
        changes_made: List of changes made during cleaning
        quality_score: Estimated quality improvement score (0.0 to 1.0)
        processing_time: Time taken for cleaning in seconds
        model_used: The model used for cleaning
        confidence_score: Confidence in the cleaning quality
    """
    original_text: str
    cleaned_text: str
    changes_made: List[str]
    quality_score: float
    processing_time: float
    model_used: str
    confidence_score: float

class TextCleaner:
    """
    Advanced text cleaner using large language models.
    
    This class provides sophisticated text cleaning capabilities using
    OpenAI's GPT models to improve text quality for TTS processing.
    
    Attributes:
        api_key: OpenAI API key for authentication
        session: aiohttp client session for HTTP requests
        config: Text cleaning configuration
    """
    
    def __init__(self, api_key: str, config: Optional[TextCleaningConfig] = None):
        """
        Initialize the text cleaner.
        
        Args:
            api_key: Valid OpenAI API key for authentication
            config: Optional text cleaning configuration
        """
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.config = config or TextCleaningConfig()
        
    async def __aenter__(self):
        """Async context manager entry - create HTTP session."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup HTTP session."""
        if self.session:
            await self.session.close()
    
    def _build_cleaning_prompt(self, text: str) -> str:
        """
        Build a comprehensive cleaning prompt for the LLM.
        
        Args:
            text: The text to be cleaned
            
        Returns:
            str: Formatted prompt for text cleaning
        """
        base_prompt = f"""
You are an expert text editor and speech preparation specialist. Your task is to clean and improve the following text for Text-to-Speech (TTS) conversion.

TEXT TO CLEAN:
{text}

CLEANING REQUIREMENTS:
- Fix grammar, punctuation, and spelling errors
- Improve sentence structure and flow for natural speech
- Ensure proper paragraph breaks and formatting
- Remove any inappropriate content or formatting
- Maintain the original meaning and intent
- Optimize for clear pronunciation and natural speech patterns

CLEANING LEVEL: {self.config.cleaning_level.upper()}
PRESERVE FORMATTING: {self.config.preserve_formatting}
FIX GRAMMAR: {self.config.fix_grammar}
IMPROVE FLOW: {self.config.improve_flow}

Please return only the cleaned text without any explanations or markdown formatting.
"""
        
        if self.config.context_prompt:
            base_prompt += f"\nADDITIONAL CONTEXT: {self.config.context_prompt}\n"
        
        return base_prompt.strip()
    
    def _build_quality_prompt(self, original: str, cleaned: str) -> str:
        """
        Build a prompt to assess the quality of cleaning.
        
        Args:
            original: Original text
            cleaned: Cleaned text
            
        Returns:
            str: Prompt for quality assessment
        """
        return f"""
You are a text quality assessment expert. Please evaluate the improvement made to this text.

ORIGINAL TEXT:
{original}

CLEANED TEXT:
{cleaned}

Please provide a JSON response with the following structure:
{{
    "quality_score": <float between 0.0 and 1.0>,
    "confidence_score": <float between 0.0 and 1.0>,
    "changes_made": [
        "description of change 1",
        "description of change 2",
        ...
    ],
    "improvement_areas": [
        "area that could be improved 1",
        "area that could be improved 2",
        ...
    ]
}}

Focus on:
- Grammar and punctuation improvements
- Sentence structure and flow
- Clarity and readability
- Suitability for speech synthesis
"""
    
    async def clean_text_with_llm(self, text: str, retries: int = 3) -> str:
        """
        Clean text using OpenAI's LLM.
        
        Args:
            text: Text to be cleaned
            retries: Number of retry attempts for failed requests
            
        Returns:
            str: Cleaned text
            
        Raises:
            Exception: If all retry attempts fail
            aiohttp.ClientError: For network-related errors
        """
        prompt = self._build_cleaning_prompt(text)
        
        for attempt in range(retries):
            try:
                logger.info(f"Cleaning text with {self.config.model} (Attempt {attempt + 1}/{retries})")
                
                response = await self.session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.config.model,
                        "messages": [
                            {"role": "system", "content": "You are an expert text editor specializing in preparing text for speech synthesis."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                )
                
                if response.status == 200:
                    result = await response.json()
                    cleaned_text = result['choices'][0]['message']['content'].strip()
                    logger.info("✅ Text cleaned successfully with LLM")
                    return cleaned_text
                elif response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                    continue
                else:
                    error_text = await response.text()
                    logger.error(f"LLM API request failed: {response.status} - {error_text}")
                    if attempt == retries - 1:
                        raise Exception(f"LLM API request failed after {retries} attempts")
                    await asyncio.sleep(2 ** attempt)
                    
            except asyncio.TimeoutError:
                logger.error(f"LLM request timeout on attempt {attempt + 1}")
                if attempt == retries - 1:
                    raise Exception("LLM request timeout after all retries")
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"LLM request failed on attempt {attempt + 1}: {e}")
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("Failed to clean text with LLM")
    
    async def assess_cleaning_quality(self, original: str, cleaned: str) -> Dict[str, Any]:
        """
        Assess the quality of text cleaning using LLM.
        
        Args:
            original: Original text
            cleaned: Cleaned text
            
        Returns:
            Dict[str, Any]: Quality assessment results
        """
        try:
            prompt = self._build_quality_prompt(original, cleaned)
            
            response = await self.session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.config.model,
                    "messages": [
                        {"role": "system", "content": "You are a text quality assessment expert."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1000
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            if response.status == 200:
                result = await response.json()
                assessment_text = result['choices'][0]['message']['content'].strip()
                
                # Parse JSON response
                try:
                    assessment = json.loads(assessment_text)
                    return assessment
                except json.JSONDecodeError:
                    logger.warning("Failed to parse quality assessment JSON, using defaults")
                    return {
                        "quality_score": 0.7,
                        "confidence_score": 0.6,
                        "changes_made": ["Text cleaned with LLM"],
                        "improvement_areas": ["Quality assessment unavailable"]
                    }
            else:
                logger.warning("Quality assessment failed, using defaults")
                return {
                    "quality_score": 0.7,
                    "confidence_score": 0.6,
                    "changes_made": ["Text cleaned with LLM"],
                    "improvement_areas": ["Quality assessment failed"]
                }
                
        except Exception as e:
            logger.error(f"Error assessing cleaning quality: {e}")
            return {
                "quality_score": 0.7,
                "confidence_score": 0.6,
                "changes_made": ["Text cleaned with LLM"],
                "improvement_areas": ["Quality assessment error"]
            }
    
    async def clean_text(self, text: str) -> CleaningResult:
        """
        Clean text and return comprehensive results.
        
        Args:
            text: Text to be cleaned
            
        Returns:
            CleaningResult: Complete cleaning results with quality assessment
        """
        start_time = time.time()
        
        try:
            # Clean the text with LLM
            cleaned_text = await self.clean_text_with_llm(text)
            
            # Assess the quality of cleaning
            assessment = await self.assess_cleaning_quality(text, cleaned_text)
            
            processing_time = time.time() - start_time
            
            return CleaningResult(
                original_text=text,
                cleaned_text=cleaned_text,
                changes_made=assessment.get("changes_made", ["Text cleaned with LLM"]),
                quality_score=assessment.get("quality_score", 0.7),
                processing_time=processing_time,
                model_used=self.config.model,
                confidence_score=assessment.get("confidence_score", 0.6)
            )
            
        except Exception as e:
            logger.error(f"Error cleaning text: {e}")
            processing_time = time.time() - start_time
            
            return CleaningResult(
                original_text=text,
                cleaned_text=text,  # Return original if cleaning fails
                changes_made=["Cleaning failed - using original text"],
                quality_score=0.0,
                processing_time=processing_time,
                model_used=self.config.model,
                confidence_score=0.0
            )
    
    async def clean_text_file(self, file_path: str, output_path: Optional[str] = None) -> CleaningResult:
        """
        Clean a text file and save the results.
        
        Args:
            file_path: Path to the input text file
            output_path: Optional output path for cleaned text
            
        Returns:
            CleaningResult: Complete cleaning results
        """
        try:
            # Read the input file
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            logger.info(f"Cleaning text file: {file_path}")
            
            # Clean the text
            result = await self.clean_text(text)
            
            # Save cleaned text if output path provided
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result.cleaned_text)
                
                logger.info(f"✅ Cleaned text saved to: {output_path}")
            
            # Log quality metrics
            logger.info(f"Quality score: {result.quality_score:.2f}")
            logger.info(f"Confidence score: {result.confidence_score:.2f}")
            logger.info(f"Processing time: {result.processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error cleaning text file: {e}")
            raise

class TextCleaningInterface:
    """
    User interface for text cleaning operations.
    
    This class provides an interactive interface for configuring
    and executing text cleaning operations.
    """
    
    def __init__(self):
        """Initialize the text cleaning interface."""
        self.config = TextCleaningConfig()
    
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
    
    def configure_cleaning_settings(self):
        """
        Configure text cleaning settings through interactive prompts.
        """
        print("\n" + "="*30)
        print("CONFIGURE TEXT CLEANING SETTINGS")
        print("="*30)
        
        # Model selection
        print("\nAvailable models:")
        print("1. gpt-4-turbo-preview (Recommended)")
        print("2. gpt-4")
        print("3. gpt-3.5-turbo")
        
        models = {
            "1": "gpt-4-turbo-preview",
            "2": "gpt-4",
            "3": "gpt-3.5-turbo"
        }
        
        while True:
            choice = input("Select model (1-3): ").strip()
            if choice in models:
                self.config.model = models[choice]
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
                self.config.cleaning_level = levels[choice]
                break
            else:
                print("Please enter a number between 1 and 3.")
        
        # Feature toggles
        self.config.preserve_formatting = input("Preserve original formatting? (y/n): ").strip().lower() == 'y'
        self.config.fix_grammar = input("Fix grammar and punctuation? (y/n): ").strip().lower() == 'y'
        self.config.improve_flow = input("Improve sentence flow? (y/n): ").strip().lower() == 'y'
        
        # Custom context prompt
        context = input("Enter custom context prompt (optional): ").strip()
        if context:
            self.config.context_prompt = context
    
    def get_file_path(self) -> Optional[str]:
        """
        Get the input file path from user input.
        
        Returns:
            Optional[str]: Valid file path or None if not provided
        """
        print("\nEnter the path to your text file:")
        print("Supported formats: .txt, .md, .json, .csv")
        
        file_path = input("File path: ").strip()
        
        if not file_path:
            return None
        
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found.")
            return None
        
        return file_path
    
    def get_output_path(self) -> Optional[str]:
        """
        Get the output file path from user input.
        
        Returns:
            Optional[str]: Output file path or None for auto-generated path
        """
        print("\nOutput options:")
        print("1. Auto-generate output path")
        print("2. Specify custom output path")
        
        while True:
            choice = input("Select option (1 or 2): ").strip()
            if choice == "1":
                return None
            elif choice == "2":
                output_path = input("Enter output file path: ").strip()
                return output_path
            else:
                print("Please enter 1 or 2.")

async def main():
    """
    Main function for text cleaning workflow.
    
    This function handles the complete text cleaning workflow:
    1. API key validation
    2. Configuration setup
    3. File processing
    4. Quality assessment
    5. Results reporting
    """
    interface = TextCleaningInterface()
    
    # Get API key
    api_key = interface.get_api_key()
    if not api_key:
        print("❌ API key is required.")
        return
    
    # Configure cleaning settings
    interface.configure_cleaning_settings()
    
    # Get file path
    file_path = interface.get_file_path()
    if not file_path:
        print("❌ No valid file selected.")
        return
    
    # Get output path
    output_path = interface.get_output_path()
    if not output_path:
        # Auto-generate output path
        input_path = Path(file_path)
        output_path = input_path.with_stem(f"{input_path.stem}_cleaned")
    
    # Process the file
    async with TextCleaner(api_key, interface.config) as cleaner:
        try:
            result = await cleaner.clean_text_file(file_path, output_path)
            
            print("\n🎉 Text cleaning completed successfully!")
            print(f"Quality score: {result.quality_score:.2f}")
            print(f"Confidence score: {result.confidence_score:.2f}")
            print(f"Processing time: {result.processing_time:.2f}s")
            print(f"Output file: {output_path}")
            
            if result.changes_made:
                print("\nChanges made:")
                for change in result.changes_made:
                    print(f"  • {change}")
                    
        except Exception as e:
            print(f"\n❌ Text cleaning failed: {e}")
            print("Check the log file for more details.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        print("Check the log file for more details.")