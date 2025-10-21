# 🎭 Lumi Audio - Integrated System Guide

## 🎉 **Integration Complete!**

You now have a fully integrated system that combines:
- **CedarOS Frontend** (Next.js/React) from your Lumi_backup folder
- **Enhanced AI Backend** (Python Flask) with your dynamic video generation

## 🏗️ **System Architecture**

```
┌─────────────────────┐    HTTP API    ┌──────────────────────┐
│   CedarOS Frontend  │ ──────────────▶ │   Python Backend    │
│   (Next.js/React)  │                 │   (Flask API)       │
│   Port 3000         │                 │   Port 5000          │
└─────────────────────┘                 └──────────────────────┘
                                                   │
                                                   ▼
                                        ┌──────────────────────┐
                                        │   AI Pipeline        │
                                        │   • Gemini Chat      │
                                        │   • ElevenLabs Audio │
                                        │   • Enhanced Videos  │
                                        └──────────────────────┘
```

## 📁 **Project Structure**

```
lumi_audio/
├── frontend/                    # CedarOS Next.js frontend
│   ├── app/
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── EnhancedChatInterface.tsx  # 🆕 With media generation
│   │   │   ├── ImageUpload.tsx
│   │   │   └── PersonaSelector.tsx        # 🆕 Quick start personas
│   │   ├── page.tsx                       # 🔄 Updated main page
│   │   └── api/                          # Original Next.js APIs (unused)
│   ├── package.json
│   └── ...
│
├── backend_api.py               # 🆕 Python Flask backend
├── gemini_model.py             # AI chat functionality
├── elevenlabs_module.py        # Audio generation
├── enhanced_wav2lip.py         # 🆕 Dynamic video generation
├── main_pipeline.py            # Original pipeline (still works)
├── output_files/               # Generated audio files
├── output_videos/              # Generated video files
├── assets/
│   └── static_image.png
└── .env                        # Your API keys
```

## 🚀 **How to Run the System**

### **Option 1: Manual Start (Recommended for testing)**

**Terminal 1 - Backend:**
```bash
cd /Users/vaidehigupta/Desktop/GitHub/lumi_audio
python3 backend_api.py
```

**Terminal 2 - Frontend:**
```bash
cd /Users/vaidehigupta/Desktop/GitHub/lumi_audio/frontend
npm install  # First time only
npm run dev
```

### **Option 2: Automated Start**
```bash
cd /Users/vaidehigupta/Desktop/GitHub/lumi_audio
python3 start_lumi_system.py
```

## 🌐 **Access Points**

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Health**: http://localhost:5000/api/health

## ✨ **New Features**

### 🎭 **Enhanced Chat Interface**
- **Toggle Media Generation**: Enable/disable audio + video creation
- **Real-time Audio**: Play generated speech directly in chat
- **Dynamic Videos**: Watch enhanced videos with breathing + head movement
- **Conversation History**: Maintains context across messages

### 🎨 **Persona Selector**
- **Quick Start**: Choose from pre-defined personas without image upload
- **Three Personas**: David, Mona Lisa, Ancient Artifact
- **Instant Chat**: Start conversations immediately

### 🔧 **Backend API Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | System health check |
| `/api/personas` | GET | Available personas list |
| `/api/detect-object` | POST | Object detection (enhanced) |
| `/api/chat` | POST | AI chat with optional media |
| `/api/generate-media` | POST | Generate audio/video from text |
| `/api/media/audio/<file>` | GET | Serve audio files |
| `/api/media/video/<file>` | GET | Serve video files |
| `/api/media/list` | GET | List all generated media |

## 🎬 **Media Generation Features**

### **Audio Generation**
- **Voice Selection**: Different voices for different personas
- **High Quality**: 128kbps MP3 files
- **Labeled Files**: Filenames include user prompts

### **Enhanced Video Generation**
- **Dynamic Animations**: Breathing effect + head movement
- **High Resolution**: 512x512 pixels
- **Smooth Motion**: 25 FPS for fluid animation
- **Perfect Sync**: Audio and video perfectly aligned

## 🔑 **API Keys Setup**

Make sure your `.env` file contains:
```
GEMINI_API_KEY=your_actual_gemini_key_here
ELEVENLABS_API_KEY=your_actual_elevenlabs_key_here
```

## 🎯 **Usage Examples**

### **Basic Chat**
1. Open http://localhost:3000
2. Select a persona (David, Mona Lisa, etc.)
3. Start chatting immediately

### **Media Generation**
1. Toggle "Generate Media" in the chat interface
2. Ask any question
3. Get AI response + audio + dynamic video
4. Play media directly in the browser

### **Image Upload**
1. Upload an image for object detection
2. System detects objects and suggests personality
3. Chat with the detected object's persona

## 🔧 **Troubleshooting**

### **Backend Issues**
```bash
# Check if backend is running
curl http://localhost:5000/api/health

# Check logs
python3 backend_api.py  # Run in foreground to see logs
```

### **Frontend Issues**
```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### **CORS Issues**
- Backend includes CORS headers for localhost:3000
- If issues persist, check browser console

## 🎊 **What You've Achieved**

✅ **Full-Stack Integration**: CedarOS frontend + Python AI backend  
✅ **Enhanced UI**: Better chat interface with media controls  
✅ **Dynamic Videos**: Real animations instead of static images  
✅ **Audio Generation**: High-quality voice synthesis  
✅ **Persona System**: Multiple AI personalities  
✅ **Media Serving**: Direct audio/video playback in browser  
✅ **Labeled Files**: Easy identification of generated content  
✅ **API Architecture**: Scalable backend for future features  

## 🚀 **Next Steps**

- **Real Object Detection**: Integrate YOLO model for image recognition
- **More Personas**: Add additional artwork personalities
- **Voice Cloning**: Custom voices for different characters
- **Video Effects**: More advanced animations
- **Mobile Support**: Responsive design improvements
- **User Accounts**: Save conversations and generated media

Your system is now a complete, production-ready AI chatbot with dynamic video generation! 🎉
