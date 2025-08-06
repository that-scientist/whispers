# 🎤 OpenAI Text-to-Speech Converter

A modern Python application that converts text files to speech using OpenAI's latest TTS models and API.

## ✨ Features

- **Latest OpenAI API**: Uses the new `openai` Python client (v1.0+)
- **Modern TTS Models**: Supports `tts-1`, `tts-1-hd`, and `tts-1-1106`
- **Multiple Voices**: Choose from 6 different voices (alloy, echo, fable, onyx, nova, shimmer)
- **Smart File Handling**: Automatically handles files of any size
- **Batch Processing**: Combines multiple audio chunks seamlessly
- **User-Friendly**: GUI file selection and clear progress indicators

## 📁 Application Versions

### `app_simple.py` - Simple Version
- For files under 4096 characters
- Single API call
- No dependencies beyond `openai`
- Perfect for most use cases

### `app_modern.py` - Full-Featured Version
- Handles files of any size
- Automatic chunking and audio combination
- Async processing for better performance
- Includes `pydub` for audio manipulation

### `app_improved.py` & `app_batch.py` - Legacy Versions
- Previous implementations using `aiohttp`
- Still functional but not recommended for new projects

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your API key** (optional):
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

3. **Run the application**:
   ```bash
   python app_simple.py    # For small files
   # or
   python app_modern.py    # For any file size
   ```

## 🎙️ Available Models

- **tts-1**: Fast, standard quality
- **tts-1-hd**: Slower, high definition
- **tts-1-1106**: Latest, best quality (recommended)

## 🎭 Available Voices

- **alloy**: Neutral, professional
- **echo**: Warm, friendly
- **fable**: Storytelling voice
- **onyx**: Deep, authoritative
- **nova**: Bright, energetic
- **shimmer**: Soft, gentle

## 📋 Requirements

- Python 3.7+
- OpenAI API key
- Internet connection

## 🔧 Dependencies

- `openai>=1.0.0` - Modern OpenAI Python client
- `pydub>=0.25.0` - Audio file manipulation (for batch processing)
- `tkinter` - GUI components (usually built-in)

## 💡 Usage Tips

1. **For best quality**: Use `tts-1-1106` model
2. **For speed**: Use `tts-1` model
3. **For large files**: Use `app_modern.py`
4. **For small files**: Use `app_simple.py`

## 🔄 Migration from Old Versions

The original `app.py`, `app2.py`, and `app3.py` used:
- Legacy `aiohttp` requests
- Manual text chunking
- Complex audio combination
- Limited voice options

The new versions use:
- Modern `openai` client
- Automatic file handling
- Better error handling
- More voice options
- Improved user experience

## 📝 Example Output

```
🎤 Simple OpenAI Text-to-Speech Converter
=============================================

🎙️ Available TTS Models:
1. tts-1 (Fast, Standard Quality)
2. tts-1-hd (Slower, High Definition)
3. tts-1-1106 (Latest, Best Quality)
Select voice model (1-3): 3

🎭 Available Voices:
1. Alloy
2. Echo
3. Fable
4. Onyx
5. Nova
6. Shimmer
Select voice (1-6): 5

🎯 Settings:
   Model: tts-1-1106
   Voice: nova
   Input: /path/to/your/file.txt

📄 File size: 2048 characters
🎙️ Model: tts-1-1106
🎭 Voice: nova
📁 Output: /path/to/your/file.aac

✅ Successfully created audio file: /path/to/your/file.aac
📊 File size: 156789 bytes

🎉 Conversion completed successfully!
```
