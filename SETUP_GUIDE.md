# 🎨 Dynamic Museum Chatbot Setup Guide

This project creates talking avatar videos of famous artworks using AI technologies:
- **Google Gemini**: Generates personality-based responses
- **ElevenLabs**: Text-to-speech with different voices
- **Wav2Lip**: Creates lip-synchronized videos

## ✅ Current Status

### What's Working:
- ✅ Basic demo functionality (simulated versions)
- ✅ Python environment with required packages
- ✅ Wav2Lip model checkpoint (wav2lip_gan.pth) ✓ Downloaded
- ✅ Static image for video generation

### What You Need to Set Up:

## 🔧 Setup Instructions

### 1. API Keys Setup
Create a `.env` file in the project root with your API keys:

```bash
# Create .env file
touch .env
```

Add the following content to `.env`:
```
# Google Gemini API Key
# Get your key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# ElevenLabs API Key  
# Get your key from: https://elevenlabs.io/app/settings/api-keys
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### 2. Install Additional Dependencies (if needed)
The project needs these packages for Wav2Lip:
```bash
pip install opencv-python torch torchvision tqdm
```

### 3. Install FFmpeg (for video processing)
```bash
# macOS
brew install ffmpeg

# Or download from: https://ffmpeg.org/download.html
```

## 🚀 How to Run

### Option 1: Simple Demo (No API Keys Required)
```bash
python simple_demo.py
```
This runs with simulated AI responses and creates text files instead of actual audio/video.

### Option 2: Full Pipeline (Requires API Keys)
```bash
python main_pipeline.py
```
This uses real AI services to create actual talking videos.

### Option 3: Test Script (Automated Testing)
```bash
python test_demo.py
```
Runs automated tests to verify functionality.

## 🎭 Available Personalities

1. **Statue of David**: Confident, dramatic, Renaissance masculine voice
2. **Mona Lisa**: Mysterious, elegant, feminine voice  
3. **Ancient Artifact**: Calm, wise, neutral voice (default for other objects)

## 📁 Project Structure

```
lumi_audio/
├── main_pipeline.py          # Main application with API integrations
├── simple_demo.py           # Demo version without APIs
├── test_demo.py            # Automated testing script
├── gemini_model.py         # Google Gemini integration
├── elevenlabs_module.py    # ElevenLabs text-to-speech
├── wav2lip.py             # Wav2Lip video generation
├── assets/
│   └── static_image.png   # Face image for video generation
├── Wav2Lip/
│   └── checkpoints/
│       └── wav2lip_gan.pth # ✅ Pre-trained model
├── output_files/          # Generated audio files
└── output_videos/         # Generated video files
```

## 🔍 Troubleshooting

### Common Issues:
1. **Missing API Keys**: Make sure `.env` file exists with valid keys
2. **FFmpeg Not Found**: Install FFmpeg for video processing
3. **Virtual Environment**: Make sure you're in the correct Python environment
4. **Permissions**: Ensure write permissions for output directories

### Test Commands:
```bash
# Test basic functionality
python test_demo.py

# Check if packages are installed
pip list | grep -E "(torch|opencv|elevenlabs|google)"

# Verify FFmpeg installation
ffmpeg -version
```

## 🎯 Next Steps

1. **Get API Keys**: Sign up for Google Gemini and ElevenLabs accounts
2. **Set Up .env**: Add your API keys to the environment file
3. **Test Full Pipeline**: Run `python main_pipeline.py`
4. **Customize**: Add new artwork personalities or modify existing ones

## 💡 Features

- **Dynamic Personalities**: Each artwork has unique speaking style and knowledge
- **Voice Matching**: Different voices for different character types
- **Realistic Videos**: Lip-synchronized talking avatars
- **Interactive Chat**: Continuous conversation with artworks
- **Scalable**: Easy to add new artworks and personalities
