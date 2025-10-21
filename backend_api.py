#!/usr/bin/env python3
"""
Backend API server for the Lumi Audio AI Pipeline
Integrates with the CedarOS frontend
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import time
import json
import uuid
import glob
from dotenv import load_dotenv
import threading
import queue

# Load environment variables
load_dotenv()

# Import our AI pipeline components
from gemini_model import ObjectChat 
from elevenlabs_module import generate_speech_audio
from smart_wav2lip import generate_lipsync_video_local
from custom_image_wav2lip import generate_lipsync_video_from_image
from precision_wav2lip import generate_precision_lipsync_video
from main_pipeline import simulate_object_scan

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Global storage for active chat sessions
active_sessions = {}
generation_queue = queue.Queue()

class ChatSession:
    def __init__(self, object_name, personality, is_custom=False):
        self.object_name = object_name
        self.personality = personality
        self.is_custom = is_custom
        
        if is_custom:
            # Create custom persona from the personality description
            self.persona = create_custom_persona(object_name, personality)
        else:
            # Use predefined persona
            self.persona = simulate_object_scan(object_name)
            
        self.chat_agent = ObjectChat(personality_data=self.persona)
        self.conversation_history = []
        self.created_at = time.time()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'services': {
            'gemini': bool(os.getenv("GEMINI_API_KEY")),
            'elevenlabs': bool(os.getenv("ELEVENLABS_API_KEY"))
        }
    })

def create_custom_persona(name, personality_description):
    """Create a custom persona based on user input"""
    return {
        'objectType': name,
        'personality': f"I am {name}. {personality_description}",
        'backstory': f"I am {name}, a unique entity with my own story and perspective.",
        'speakingStyle': "I speak authentically based on my personality and nature.",
        'interests': ["conversation", "sharing my perspective", "connecting with others"],
        'voice_id': "t5skN5jHed0hDk7ZanZS"  # Default neutral voice
    }

@app.route('/api/detect-person', methods=['POST'])
def detect_person():
    """Gemini-powered person detection from camera image"""
    try:
        import google.generativeai as genai
        
        # Configure Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        data = request.get_json()
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Convert base64 to image for Gemini
        import base64
        from PIL import Image
        from io import BytesIO
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # Prepare prompt for person detection
        prompt = """Look at this image and identify the person, character, or being shown. This could be:
        - A famous historical figure
        - A fictional character
        - A celebrity or public figure
        - An artwork or painting subject
        - A mythological figure
        
        Respond with just the name of the person/character. If you cannot identify them specifically, describe what type of person they appear to be (e.g., "Young Artist", "Business Person", "Student", etc.)."""
        
        # Generate content with image
        response = model.generate_content([prompt, image])
        
        if not response.text:
            raise Exception("Gemini did not return a response")
        
        # Clean the response
        person_name = response.text.strip()
        
        # Remove quotes if present
        if person_name.startswith('"') and person_name.endswith('"'):
            person_name = person_name[1:-1].strip()
        if person_name.startswith("'") and person_name.endswith("'"):
            person_name = person_name[1:-1].strip()
        
        # If empty, use default
        if not person_name:
            person_name = "Interesting Individual"
        
        return jsonify({
            'personName': person_name,
            'label': person_name,  # For compatibility
            'confidence': 0.85,
            'detectionMethod': 'gemini-vision'
        })
        
    except Exception as e:
        print(f"Error in person detection: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-custom-persona', methods=['POST'])
def create_custom_persona_endpoint():
    """Create a custom persona from user input"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        personality = data.get('personality', '').strip()
        
        if not name or not personality:
            return jsonify({'error': 'Both name and personality description are required'}), 400
        
        # Create custom persona
        custom_persona = create_custom_persona(name, personality)
        
        result = {
            "objects": [
                {
                    "class": name,
                    "confidence": 1.0,
                    "bbox": {
                        "x": 100,
                        "y": 100,
                        "width": 200,
                        "height": 300
                    }
                }
            ],
            "mainObject": name,
            "suggestedPersonality": custom_persona['personality'],
            "customPersona": True
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in create_custom_persona: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/detect-object', methods=['POST'])
def detect_object():
    """Object detection endpoint - enhanced version"""
    try:
        # For now, we'll simulate object detection
        # You can integrate actual YOLO detection later
        
        # Get the object name from form data or use a default
        if 'objectName' in request.form:
            object_name = request.form['objectName']
        else:
            # Default objects for demo
            object_name = "David"  # or "Mona Lisa"
        
        # Simulate object detection result
        persona = simulate_object_scan(object_name)
        
        result = {
            "objects": [
                {
                    "class": object_name,
                    "confidence": 0.95,
                    "bbox": {
                        "x": 100,
                        "y": 100,
                        "width": 200,
                        "height": 300
                    }
                }
            ],
            "mainObject": object_name,
            "suggestedPersonality": persona['personality']
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in detect_object: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Enhanced chat endpoint with audio/video generation"""
    try:
        data = request.get_json()
        message = data.get('message')
        object_name = data.get('objectName')
        personality = data.get('personality')
        conversation_history = data.get('conversationHistory', [])
        generate_media = data.get('generateMedia', False)  # New option
        is_custom = data.get('isCustom', False)  # New option for custom personas
        uploaded_image = data.get('uploadedImage')  # Image data (camera capture or manual upload)
        use_precision_lipsync = data.get('usePrecisionLipSync', False)  # Use precision lip-sync
        source_image_type = data.get('sourceImageType', 'none')  # Track image source
        
        if not all([message, object_name, personality]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create or get chat session
        session_key = f"{object_name}_{hash(personality)}"  # Use hash to handle custom personalities
        if session_key not in active_sessions:
            active_sessions[session_key] = ChatSession(object_name, personality, is_custom)
        
        session = active_sessions[session_key]
        
        # Generate AI response
        ai_response = session.chat_agent.chat(message)
        
        # Update conversation history
        session.conversation_history.append([message, ai_response])
        
        response_data = {
            'response': ai_response,
            'character': object_name,
            'personality': personality,
            'conversationHistory': session.conversation_history[-10:],  # Keep last 10 exchanges
            'mediaGenerated': False
        }
        
        # Generate media if requested
        print(f"🔍 DEBUG: generate_media = {generate_media}")
        if generate_media:
            print("🎬 Starting media generation...")
            try:
                # Generate audio
                audio_path = generate_speech_audio(
                    ai_response, 
                    voice_id=session.persona.get("voice_id", "t5skN5jHed0hDk7ZanZS"),
                    output_dir="output_files",
                    user_prompt=message
                )
                
                print(f"🎵 Audio generated: {audio_path}")
                if audio_path:
                    # Generate video with appropriate method based on image source
                    if uploaded_image:
                        if source_image_type == 'camera_capture':
                            # Use precision lip-sync for camera-captured images
                            print(f"📸 Using Precision Lip-Sync with camera-captured image of {object_name}")
                            video_path = generate_precision_lipsync_video(
                                audio_path,
                                uploaded_image,
                                output_dir="output_videos", 
                                user_prompt=message
                            )
                        elif use_precision_lipsync:
                            # Use precision lip-sync for manually uploaded images when requested
                            print(f"🎯 Using Precision Lip-Sync with uploaded image")
                            video_path = generate_precision_lipsync_video(
                                audio_path,
                                uploaded_image,
                                output_dir="output_videos", 
                                user_prompt=message
                            )
                        else:
                            # Use custom image method for regular uploads
                            print(f"🖼️  Using custom image for video generation")
                            video_path = generate_lipsync_video_from_image(
                                audio_path,
                                uploaded_image,
                                output_dir="output_videos", 
                                user_prompt=message
                            )
                    else:
                        # Use default static image when no custom image provided
                        print("🎭 Using default template for video generation")
                        video_path = generate_lipsync_video_local(
                            audio_path, 
                            output_dir="output_videos",
                            user_prompt=message
                        )
                    
                    print(f"🎬 Video generated: {video_path}")
                    if video_path:
                        print("✅ Media generation successful, updating response data")
                        response_data.update({
                            'mediaGenerated': True,
                            'audioFile': os.path.basename(audio_path),
                            'videoFile': os.path.basename(video_path),
                            'audioUrl': f'/api/media/audio/{os.path.basename(audio_path)}',
                            'videoUrl': f'/api/media/video/{os.path.basename(video_path)}'
                        })
                    else:
                        print("❌ Video generation failed")
                else:
                    print("❌ Audio generation failed")
                        
            except Exception as media_error:
                print(f"Media generation error: {media_error}")
                response_data['mediaError'] = str(media_error)
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-media', methods=['POST'])
def generate_media():
    """Dedicated endpoint for generating audio/video from text"""
    try:
        data = request.get_json()
        text = data.get('text')
        object_name = data.get('objectName')
        user_prompt = data.get('userPrompt', 'Generated content')
        
        if not text or not object_name:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get persona for voice selection
        persona = simulate_object_scan(object_name)
        voice_id = persona.get("voice_id", "t5skN5jHed0hDk7ZanZS")
        
        # Generate audio
        audio_path = generate_speech_audio(
            text, 
            voice_id=voice_id,
            output_dir="output_files",
            user_prompt=user_prompt
        )
        
        if not audio_path:
            return jsonify({'error': 'Failed to generate audio'}), 500
        
        # Generate video
        video_path = generate_lipsync_video_local(
            audio_path, 
            output_dir="output_videos",
            user_prompt=user_prompt
        )
        
        if not video_path:
            return jsonify({'error': 'Failed to generate video'}), 500
        
        return jsonify({
            'success': True,
            'audioFile': os.path.basename(audio_path),
            'videoFile': os.path.basename(video_path),
            'audioUrl': f'/api/media/audio/{os.path.basename(audio_path)}',
            'videoUrl': f'/api/media/video/{os.path.basename(video_path)}'
        })
        
    except Exception as e:
        print(f"Error in generate_media: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/media/audio/<filename>')
def serve_audio(filename):
    """Serve audio files"""
    try:
        file_path = os.path.join('output_files', filename)
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='audio/mpeg')
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/media/video/<filename>')
def serve_video(filename):
    """Serve video files"""
    try:
        file_path = os.path.join('output_videos', filename)
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='video/mp4')
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/media/list', methods=['GET'])
def list_media():
    """List all generated media files"""
    try:
        audio_files = []
        video_files = []
        
        # List audio files
        if os.path.exists('output_files'):
            for file in glob.glob('output_files/*.mp3'):
                filename = os.path.basename(file)
                file_size = os.path.getsize(file)
                audio_files.append({
                    'filename': filename,
                    'size': file_size,
                    'url': f'/api/media/audio/{filename}',
                    'created': os.path.getctime(file)
                })
        
        # List video files
        if os.path.exists('output_videos'):
            for file in glob.glob('output_videos/*.mp4'):
                filename = os.path.basename(file)
                file_size = os.path.getsize(file)
                video_files.append({
                    'filename': filename,
                    'size': file_size,
                    'url': f'/api/media/video/{filename}',
                    'created': os.path.getctime(file)
                })
        
        return jsonify({
            'audio': sorted(audio_files, key=lambda x: x['created'], reverse=True),
            'video': sorted(video_files, key=lambda x: x['created'], reverse=True)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/personas', methods=['GET'])
def get_personas():
    """Get available personas/characters"""
    personas = []
    
    # Get all available personas
    for obj_name in ["David", "Mona Lisa", "Ancient Artifact"]:
        persona = simulate_object_scan(obj_name)
        personas.append({
            'name': obj_name,
            'objectType': persona['objectType'],
            'personality': persona['personality'],
            'backstory': persona['backstory'],
            'speakingStyle': persona['speakingStyle'],
            'interests': persona['interests']
        })
    
    return jsonify({'personas': personas})

if __name__ == '__main__':
    print("🚀 Starting Lumi Audio Backend API Server...")
    print(f"🔑 Gemini API Key: {'✅ Found' if os.getenv('GEMINI_API_KEY') else '❌ Missing'}")
    print(f"🔑 ElevenLabs API Key: {'✅ Found' if os.getenv('ELEVENLABS_API_KEY') else '❌ Missing'}")
    print("🌐 Server will run on http://localhost:5001")
    print("🎬 Frontend should connect to this backend for AI features")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
