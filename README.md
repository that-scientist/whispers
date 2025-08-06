# Unified OpenAI Audio Processing Tool

A comprehensive Python tool for both **Text-to-Speech (TTS)** and **Audio Transcription** using OpenAI's APIs. Features a unified interface with enhanced UX and robust error handling.

## 🚀 Features

### Core Capabilities
- **🎤 Text-to-Speech**: Convert text files to speech with multiple voices and speeds
- **📝 Audio Transcription**: Transcribe audio files to text with language detection
- **🔄 Unified Interface**: Single tool for both TTS and transcription
- **⚡ Real-time Processing**: Immediate TTS conversion
- **📦 Batch Processing**: File upload for transcription

### TTS Features
- **Multiple Models**: `tts-1` (fast) and `tts-1-hd` (high quality)
- **6 Voice Options**: alloy, echo, fable, onyx, nova, shimmer
- **Adjustable Speed**: 0.75x to 1.5x playback speed
- **Large File Support**: Automatic text chunking for files >4096 characters
- **Multiple Formats**: AAC, MP3, Opus, FLAC output formats

### Transcription Features
- **File Upload**: Support for mp3, mp4, mpeg, mpga, m4a, wav, webm
- **Language Detection**: Auto-detect or specify language
- **Context Prompts**: Optional prompts to improve accuracy
- **Multiple Outputs**: JSON with metadata and plain text extraction

### Enhanced UX
- **Interactive Configuration**: Step-by-step setup with clear options
- **Progress Tracking**: Real-time status updates and file information
- **Comprehensive Logging**: Detailed logs for debugging and monitoring
- **Error Handling**: Robust error handling with retry logic and rate limiting
- **Flexible Output**: Custom output directories and file naming

## 📋 Requirements

### System Requirements
- Python 3.8+
- FFmpeg (for audio processing)
- Internet connection for OpenAI API

### Python Dependencies
```
aiohttp>=3.8.0,<4.0.0
typing-extensions>=4.0.0
```

## 🛠️ Installation

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd whispers
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install FFmpeg** (if not already installed)
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # macOS
   brew install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

5. **Set up your OpenAI API key**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

## 🎯 Usage

### Basic Usage
```bash
python main.py
```

### With Command Line Arguments
```bash
python main.py path/to/your/file.txt
python main.py path/to/your/audio.mp3
```

### Interactive Mode
The application will guide you through:

1. **Processing Mode Selection**
   - Text-to-Speech (Real-time)
   - Audio Transcription (Batch)

2. **Configuration**
   - **For TTS**: Model, voice, speed selection
   - **For Transcription**: Language, optional prompts

3. **File Selection**
   - Text files for TTS
   - Audio files for transcription

4. **Output Configuration**
   - Choose output directory

## 📁 File Structure

```
whispers/
├── main.py                    # 🆕 Unified audio processor
├── test_main.py              # 🆕 Test suite
├── config.json               # Configuration file
├── requirements.txt           # Python dependencies
├── README.md                 # This file
├── IMPROVEMENTS.md           # Improvement summary
├── mnemonics.txt             # Sample text file
├── *.aac                     # Generated audio files
└── *_transcription.json      # Transcription results
```

## 🔧 Configuration Options

### TTS Models
- **tts-1**: Fast, optimized for real-time text-to-speech
- **tts-1-hd**: High definition, optimized for quality

### Voices
- **alloy**: Neutral, balanced voice
- **echo**: Deep, authoritative voice
- **fable**: Warm, storytelling voice
- **onyx**: Serious, professional voice
- **nova**: Bright, energetic voice
- **shimmer**: Soft, gentle voice

### Speed Options
- **0.75x**: Slow
- **1.0x**: Normal
- **1.25x**: Fast
- **1.5x**: Very Fast

### Transcription Languages
- **Auto-detect**: Automatically detect language
- **English**: Specify English
- **Spanish**: Specify Spanish
- **French**: Specify French
- **German**: Specify German

### Supported Audio Formats
- **mp3**: Most common format
- **mp4**: Video files with audio
- **mpeg**: MPEG audio
- **mpga**: MPEG audio
- **m4a**: AAC audio
- **wav**: Uncompressed audio
- **webm**: Web audio format

## 📊 Logging

The application creates detailed log files:
- `audio_processor.log`: Processing logs for both TTS and transcription

Log levels include:
- **INFO**: General progress and status
- **WARNING**: Rate limiting and retries
- **ERROR**: Failed requests and processing errors

## 🚨 Error Handling

### Common Issues and Solutions

#### API Key Issues
```
❌ API key is required.
```
**Solution**: Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-key-here"
```

#### Rate Limiting
```
⚠️ Rate limited. Waiting 60 seconds...
```
**Solution**: The application automatically handles rate limiting with exponential backoff.

#### File Not Found
```
❌ File not found: path/to/file.txt
```
**Solution**: Check the file path and ensure the file exists.

#### Large File Processing
For TTS files exceeding 4096 characters, the application automatically splits them into chunks and processes them separately.

## 🔄 Rate Limits

OpenAI API rate limits:
- **TTS (tts-1)**: 100 requests per minute
- **TTS (tts-1-hd)**: 10 requests per minute
- **Transcription**: Varies by file size and complexity

The application automatically manages these limits with appropriate delays.

## 📈 Performance Tips

1. **Use tts-1 for speed**: Choose the normal model for faster TTS processing
2. **Optimize audio files**: Use compressed formats (mp3, m4a) for transcription
3. **Monitor logs**: Check log files for performance insights
4. **Batch processing**: Process multiple files efficiently

## 🧪 Testing

Run the test suite to verify functionality:
```bash
python test_main.py
```

This will test:
- Module imports
- Configuration loading
- Text splitting
- File operations
- Interface components
- Processing modes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for providing the TTS and Whisper APIs
- The open-source community for various Python libraries
- Contributors and users who provided feedback

## 📞 Support

For issues, questions, or feature requests:
1. Check the log files for detailed error information
2. Review the configuration options
3. Ensure all dependencies are properly installed
4. Verify your OpenAI API key is valid and has sufficient credits

---

**Note**: This tool requires an active OpenAI API key with TTS and Whisper access. Please ensure you have sufficient API credits for your processing needs.
