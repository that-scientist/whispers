# 🧹 Advanced Text Cleaning with Large Language Models

## Overview

The text cleaning module provides **sophisticated text preprocessing capabilities** using OpenAI's GPT-4.1 and other large language models to dramatically improve text quality before Text-to-Speech conversion.

## 🚀 Key Features

### **Advanced Text Processing**
- **Grammar and punctuation correction** using GPT-4
- **Sentence structure improvement** for natural speech flow
- **Context-aware text enhancement** with custom prompts
- **Multiple cleaning strategies** (light, medium, aggressive)
- **Quality scoring and validation** for cleaning results

### **Integration with TTS**
- **Seamless integration** with the main audio processing tool
- **Automatic text cleaning** before TTS conversion
- **Quality-based decisions** (only use cleaned text if quality is high)
- **Temporary file handling** for cleaned text
- **Comprehensive logging** of cleaning operations

### **Flexible Configuration**
- **Multiple LLM models** (GPT-4, GPT-4 Turbo, GPT-3.5 Turbo)
- **Adjustable cleaning levels** (light, medium, aggressive)
- **Feature toggles** (grammar, flow, formatting)
- **Custom context prompts** for specialized cleaning
- **Quality thresholds** for automatic decisions

## 📋 Installation

### **Dependencies**
```bash
pip install openai aiohttp
```

### **Optional Enhanced Features**
```bash
pip install rich click  # For enhanced UI
```

## 🎯 Usage Examples

### **Standalone Text Cleaning**
```bash
python text_cleaner.py
```

### **Integrated with TTS Processing**
```bash
python main.py path/to/your/text_file.txt
# Then select "Enable text cleaning" during configuration
```

### **Programmatic Usage**
```python
from text_cleaner import TextCleaner, TextCleaningConfig

# Configure text cleaning
config = TextCleaningConfig(
    model="gpt-4-turbo-preview",
    cleaning_level="medium",
    fix_grammar=True,
    improve_flow=True
)

# Clean text
async with TextCleaner(api_key, config) as cleaner:
    result = await cleaner.clean_text("Your text here...")
    print(f"Quality score: {result.quality_score}")
    print(f"Cleaned text: {result.cleaned_text}")
```

## 🔧 Configuration Options

### **TextCleaningConfig**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | str | "gpt-4-turbo-preview" | OpenAI model for cleaning |
| `temperature` | float | 0.1 | Sampling temperature (0.0-2.0) |
| `max_tokens` | int | 4000 | Maximum response tokens |
| `cleaning_level` | str | "medium" | Cleaning intensity |
| `preserve_formatting` | bool | True | Keep original formatting |
| `fix_grammar` | bool | True | Fix grammar and punctuation |
| `improve_flow` | bool | True | Improve sentence flow |
| `context_prompt` | str | None | Custom context for cleaning |

### **Cleaning Levels**

| Level | Description | Use Case |
|-------|-------------|----------|
| **Light** | Minor corrections only | Quick fixes, preserve style |
| **Medium** | Grammar and flow improvements | General text enhancement |
| **Aggressive** | Major restructuring | Complete text overhaul |

### **Available Models**

| Model | Speed | Quality | Cost | Best For |
|-------|-------|---------|------|----------|
| **gpt-4-turbo-preview** | Fast | High | Medium | General use |
| **gpt-4** | Medium | Highest | High | Critical quality |
| **gpt-3.5-turbo** | Fastest | Good | Low | Budget-friendly |

## 📊 Quality Assessment

### **CleaningResult**

The text cleaner provides comprehensive quality assessment:

```python
@dataclass
class CleaningResult:
    original_text: str          # Original input text
    cleaned_text: str          # Improved text
    changes_made: List[str]    # List of changes made
    quality_score: float       # Quality improvement (0.0-1.0)
    processing_time: float     # Time taken in seconds
    model_used: str           # Model used for cleaning
    confidence_score: float   # Confidence in quality (0.0-1.0)
```

### **Quality Metrics**

- **Quality Score**: Overall improvement assessment (0.0-1.0)
- **Confidence Score**: Reliability of the cleaning (0.0-1.0)
- **Processing Time**: Time taken for cleaning operation
- **Changes Made**: Detailed list of improvements

## 🔄 Integration with TTS Workflow

### **Automatic Integration**

When text cleaning is enabled in the TTS workflow:

1. **Text Reading**: Read the input text file
2. **Quality Assessment**: Evaluate if cleaning is needed
3. **LLM Processing**: Clean text using selected model
4. **Quality Validation**: Only use cleaned text if quality > 0.5
5. **Temporary File**: Create cleaned text file for TTS
6. **TTS Processing**: Convert cleaned text to speech
7. **Cleanup**: Remove temporary files

### **Configuration Flow**

```
TTS Configuration
├── Model Selection (tts-1, tts-1-hd)
├── Voice Selection (alloy, echo, fable, etc.)
├── Speed Configuration (0.75x - 1.5x)
└── Text Cleaning Options
    ├── Enable/Disable Cleaning
    ├── Model Selection (GPT-4, GPT-3.5, etc.)
    ├── Cleaning Level (Light, Medium, Aggressive)
    ├── Feature Toggles (Grammar, Flow, Formatting)
    └── Custom Context Prompt
```

## 🎨 Advanced Features

### **Context-Aware Cleaning**

Provide custom context for specialized cleaning:

```python
config = TextCleaningConfig(
    context_prompt="This is technical documentation for software developers"
)
```

### **Quality-Based Decisions**

The system automatically decides whether to use cleaned text:

- **Quality Score > 0.5**: Use cleaned text
- **Quality Score ≤ 0.5**: Use original text
- **Cleaning Failed**: Fall back to original text

### **Batch Processing**

Process multiple files with consistent settings:

```python
async with TextCleaner(api_key, config) as cleaner:
    for file_path in text_files:
        result = await cleaner.clean_text_file(file_path)
        print(f"{file_path}: {result.quality_score:.2f}")
```

## 📈 Performance Characteristics

### **Processing Speed**

| Model | Average Time | Tokens/Second | Best For |
|-------|-------------|---------------|----------|
| GPT-4 Turbo | ~2-5 seconds | ~1000 | General use |
| GPT-4 | ~5-10 seconds | ~500 | High quality |
| GPT-3.5 Turbo | ~1-3 seconds | ~1500 | Fast processing |

### **Quality vs Speed Trade-offs**

- **High Quality**: GPT-4 with aggressive cleaning
- **Balanced**: GPT-4 Turbo with medium cleaning
- **Fast Processing**: GPT-3.5 Turbo with light cleaning

## 🔒 Error Handling

### **Robust Error Recovery**

- **API Failures**: Automatic retry with exponential backoff
- **Rate Limiting**: Intelligent waiting and retry logic
- **Network Issues**: Graceful degradation to original text
- **Quality Issues**: Fallback to original if cleaning quality is poor

### **Comprehensive Logging**

```python
logger.info("🧹 Cleaning text before TTS processing...")
logger.info(f"✅ Text cleaned successfully (quality: {result.quality_score:.2f})")
logger.warning(f"⚠️ Text cleaning quality too low ({result.quality_score:.2f})")
logger.error(f"❌ Text cleaning failed: {e}")
```

## 🧪 Testing and Validation

### **Quality Testing**

```python
# Test cleaning quality
async def test_cleaning_quality():
    config = TextCleaningConfig(cleaning_level="medium")
    async with TextCleaner(api_key, config) as cleaner:
        result = await cleaner.clean_text(test_text)
        assert result.quality_score > 0.5
        assert result.confidence_score > 0.6
```

### **Performance Testing**

```python
# Test processing speed
async def test_processing_speed():
    start_time = time.time()
    result = await cleaner.clean_text(large_text)
    processing_time = time.time() - start_time
    assert processing_time < 30  # Should complete within 30 seconds
```

## 🔮 Future Enhancements

### **Planned Features**

- **Multi-language Support**: Clean text in multiple languages
- **Style Preservation**: Maintain author's writing style
- **Domain-Specific Cleaning**: Specialized cleaning for different content types
- **Batch Optimization**: Parallel processing for multiple files
- **Quality Prediction**: Predict cleaning quality before processing

### **Advanced Capabilities**

- **Voice-Specific Optimization**: Clean text for specific TTS voices
- **Emotion Preservation**: Maintain emotional tone in cleaned text
- **Format Detection**: Automatic detection of text format and style
- **Custom Models**: Support for fine-tuned models

## 📚 Use Cases

### **Content Creation**

- **Blog Posts**: Clean and improve blog content for podcast narration
- **Technical Documentation**: Enhance technical text for clear pronunciation
- **Marketing Copy**: Optimize marketing text for voice-over
- **Educational Content**: Improve educational materials for audio learning

### **Business Applications**

- **Corporate Communications**: Clean internal communications for audio
- **Training Materials**: Enhance training content for audio delivery
- **Customer Service**: Improve customer-facing text for voice systems
- **Legal Documents**: Clean legal text for accessibility

### **Personal Use**

- **Notes and Journals**: Clean personal notes for audio playback
- **Creative Writing**: Enhance creative writing for narration
- **Language Learning**: Improve text for pronunciation practice
- **Accessibility**: Make text more accessible through audio

## 🤝 Contributing

### **Development Setup**

```bash
git clone <repository>
cd audio-processing-tool
git checkout feature/text-cleaning-with-llm
pip install -r requirements.txt
```

### **Testing**

```bash
# Run text cleaning tests
python -m pytest tests/test_text_cleaner.py

# Run integration tests
python -m pytest tests/test_integration.py
```

### **Code Quality**

- **Type Hints**: Comprehensive type annotations
- **Documentation**: Detailed docstrings and comments
- **Error Handling**: Robust exception handling
- **Logging**: Comprehensive logging throughout

## 📄 License

This text cleaning module maintains the same license as the main project.

---

**Transform your text quality with AI-powered cleaning!** The text cleaning module provides professional-grade text enhancement using the latest large language models for superior TTS results. 🚀