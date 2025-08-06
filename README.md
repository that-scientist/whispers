# Enhanced OpenAI Text-to-Speech Converter

A comprehensive Python tool for converting text files to speech using OpenAI's TTS API with advanced features, better error handling, and improved user experience.

## 🚀 Features

### Core Features
- **Multiple TTS Models**: Support for both `tts-1` (fast) and `tts-1-hd` (high quality)
- **6 Voice Options**: alloy, echo, fable, onyx, nova, shimmer
- **Adjustable Speed**: 0.75x to 1.5x playback speed
- **Multiple Formats**: AAC, MP3, Opus, FLAC output formats
- **Large File Support**: Automatic text chunking for files exceeding 4096 characters
- **Batch Processing**: Process multiple files with consistent settings

### Enhanced UX
- **Interactive Configuration**: Step-by-step setup with clear options
- **Progress Tracking**: Real-time progress indicators and status updates
- **Comprehensive Logging**: Detailed logs for debugging and monitoring
- **Error Handling**: Robust error handling with retry logic and rate limiting
- **Flexible Output**: Custom output directories and file naming

### API Improvements
- **Rate Limiting**: Automatic rate limit management with exponential backoff
- **Retry Logic**: Configurable retry attempts with intelligent backoff
- **Timeout Handling**: Proper timeout management for long requests
- **Response Validation**: Comprehensive API response validation

## 📋 Requirements

### System Requirements
- Python 3.8+
- FFmpeg (for audio processing)
- Internet connection for OpenAI API

### Python Dependencies
```
aiohttp>=3.8.0
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

### Single File Conversion

#### Basic Usage
```bash
python app_enhanced.py
```

#### With Command Line Arguments
```bash
python app_enhanced.py path/to/your/file.txt
```

#### Interactive Mode
The application will guide you through:
1. **API Key Setup**: Enter your OpenAI API key or use environment variable
2. **File Selection**: Choose the text file to convert
3. **Model Selection**: Choose between normal (tts-1) or high-definition (tts-1-hd)
4. **Voice Selection**: Choose from 6 available voices
5. **Speed Configuration**: Set playback speed (0.75x to 1.5x)
6. **Output Configuration**: Choose output location

### Batch Processing

#### Process All Files in a Directory
```bash
python app_batch_enhanced.py
```

#### Features
- Automatically finds `.txt`, `.md`, and `.text` files
- Consistent settings across all files
- Detailed progress tracking
- Summary report with success/failure statistics

### Configuration

#### Environment Variables
```bash
export OPENAI_API_KEY="your-api-key-here"
```

#### Configuration File
Edit `config.json` to customize default settings:
```json
{
    "default_model": "tts-1",
    "default_voice": "alloy",
    "default_speed": 1.0,
    "default_format": "aac"
}
```

## 📁 File Structure

```
whispers/
├── app_enhanced.py          # Enhanced single-file converter
├── app_batch_enhanced.py    # Enhanced batch processor
├── app.py                   # Original basic converter
├── app_improved.py          # Improved version
├── app_batch.py             # Original batch processor
├── config.json              # Configuration file
├── requirements.txt          # Python dependencies
├── README.md               # This file
├── mnemonics.txt           # Sample text file
└── *.aac                   # Generated audio files
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

### Output Formats
- **AAC**: Recommended, good quality and size
- **MP3**: Widely compatible
- **Opus**: Good compression
- **FLAC**: Lossless quality

## 📊 Logging

The application creates detailed log files:
- `tts_converter.log`: Single file conversion logs
- `batch_tts_converter.log`: Batch processing logs

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
For files exceeding 4096 characters, the application automatically splits them into chunks and processes them separately.

## 🔄 Rate Limits

OpenAI TTS API rate limits:
- **tts-1**: 100 requests per minute
- **tts-1-hd**: 10 requests per minute

The application automatically manages these limits with appropriate delays.

## 📈 Performance Tips

1. **Use tts-1 for speed**: Choose the normal model for faster processing
2. **Batch processing**: Use the batch processor for multiple files
3. **Optimize text**: Remove unnecessary whitespace and formatting
4. **Monitor logs**: Check log files for performance insights

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for providing the TTS API
- The open-source community for various Python libraries
- Contributors and users who provided feedback

## 📞 Support

For issues, questions, or feature requests:
1. Check the log files for detailed error information
2. Review the configuration options
3. Ensure all dependencies are properly installed
4. Verify your OpenAI API key is valid and has sufficient credits

---

**Note**: This tool requires an active OpenAI API key with TTS access. Please ensure you have sufficient API credits for your conversion needs.
