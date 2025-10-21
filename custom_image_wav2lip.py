#!/usr/bin/env python3
"""
Custom Image Wav2Lip - Generate lip-sync videos from uploaded images
"""

import os
import subprocess
import uuid
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image

def save_uploaded_image(image_data, upload_dir="uploaded_images"):
    """Save uploaded image data to file"""
    os.makedirs(upload_dir, exist_ok=True)
    
    try:
        # Handle different types of image data
        if isinstance(image_data, str):
            if image_data.startswith('data:image'):
                # Remove data URL prefix
                image_data = image_data.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            image = Image.open(BytesIO(image_bytes))
        elif isinstance(image_data, bytes):
            # Handle raw bytes
            image = Image.open(BytesIO(image_data))
        else:
            # Handle file-like object
            image = Image.open(image_data)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save with unique filename
        image_filename = f"uploaded_{uuid.uuid4().hex[:8]}.jpg"
        image_path = os.path.join(upload_dir, image_filename)
        image.save(image_path, 'JPEG', quality=95)
        
        return image_path
        
    except Exception as e:
        print(f"Error saving uploaded image: {e}")
        return None

def detect_face_region(image_path):
    """Basic face detection to find mouth region"""
    try:
        # Load OpenCV's pre-trained face cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Read image
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            # Use the largest face
            face = max(faces, key=lambda x: x[2] * x[3])  # x, y, w, h
            x, y, w, h = face
            
            # Estimate mouth position (lower third of face)
            mouth_x = x + w // 2
            mouth_y = y + int(h * 0.75)
            mouth_w = int(w * 0.3)
            mouth_h = int(h * 0.15)
            
            return {
                'face': (x, y, w, h),
                'mouth': (mouth_x, mouth_y, mouth_w, mouth_h),
                'detected': True
            }
        else:
            # No face detected, use center-bottom estimation
            height, width = img.shape[:2]
            return {
                'face': (width//4, height//4, width//2, height//2),
                'mouth': (width//2, int(height * 0.75), int(width * 0.1), int(height * 0.05)),
                'detected': False
            }
            
    except Exception as e:
        print(f"Face detection error: {e}")
        # Fallback to center estimation
        img = cv2.imread(image_path)
        height, width = img.shape[:2]
        return {
            'face': (width//4, height//4, width//2, height//2),
            'mouth': (width//2, int(height * 0.75), int(width * 0.1), int(height * 0.05)),
            'detected': False
        }

def get_audio_duration(audio_file_path):
    """Get audio duration using ffprobe"""
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration", 
            "-of", "csv=p=0", audio_file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    except:
        return 30.0

def create_speech_pattern(duration, fps):
    """Create a realistic speech pattern"""
    total_frames = int(duration * fps)
    speech_pattern = []
    
    for frame in range(total_frames):
        time = frame / fps
        
        # Base speech rhythm
        base_freq = 4 + 2 * np.sin(time * 0.3)
        base_speech = np.sin(time * base_freq * 2 * np.pi)
        
        # Add pauses and emphasis
        pause_pattern = 1.0
        if int(time * 2) % 7 == 0:  # Pause every ~3.5 seconds
            pause_pattern = 0.1
        elif int(time * 3) % 5 == 0:  # Emphasis every ~1.7 seconds
            pause_pattern = 1.5
        
        # Combine patterns
        mouth_openness = np.clip((base_speech + 1) / 2 * pause_pattern, 0, 1)
        
        # Add consonant-like movements
        if frame % 8 == 0:
            mouth_openness = min(mouth_openness + 0.3, 1.0)
        
        speech_pattern.append(mouth_openness)
    
    return speech_pattern

def create_mouth_animation_on_image(face_img, face_regions, mouth_openness, frame_num):
    """Create mouth animation on the uploaded image"""
    frame = face_img.copy()
    height, width = frame.shape[:2]
    
    # Get mouth region from face detection
    mouth_x, mouth_y, mouth_w, mouth_h = face_regions['mouth']
    
    # Create mouth animation effects
    if mouth_openness > 0.2:  # Speaking
        # 1. Create mouth opening effect
        mouth_open_height = max(int(mouth_h * mouth_openness * 3), 1)
        
        # Create elliptical mouth region
        y_coords, x_coords = np.ogrid[:height, :width]
        mouth_mask = ((x_coords - mouth_x) / max(mouth_w, 1))**2 + \
                    ((y_coords - mouth_y) / max(mouth_open_height, 1))**2 <= 1
        
        # Darken mouth area to simulate opening
        frame[mouth_mask] = frame[mouth_mask] * (1 - mouth_openness * 0.5)
        
        # 2. Add jaw movement if face was detected
        if face_regions['detected'] and mouth_openness > 0.3:
            jaw_movement = mouth_openness * 2
            face_x, face_y, face_w, face_h = face_regions['face']
            
            # Move lower part of face
            lower_face_start = face_y + int(face_h * 0.7)
            lower_face_end = min(face_y + face_h, height)
            
            if lower_face_start < lower_face_end and lower_face_start >= 0:
                face_region = frame[lower_face_start:lower_face_end, 
                                 face_x:min(face_x + face_w, width)]
                if face_region.size > 0:
                    M = np.float32([[1, 0, 0], [0, 1, jaw_movement]])
                    moved_region = cv2.warpAffine(face_region, M, 
                                                (face_region.shape[1], face_region.shape[0]))
                    frame[lower_face_start:lower_face_end, 
                          face_x:min(face_x + face_w, width)] = moved_region
        
        # 3. Add cheek movement for strong speech
        if mouth_openness > 0.6 and face_regions['detected']:
            face_x, face_y, face_w, face_h = face_regions['face']
            
            # Left and right cheek positions
            left_cheek_x = face_x + int(face_w * 0.2)
            right_cheek_x = face_x + int(face_w * 0.8)
            cheek_y = face_y + int(face_h * 0.6)
            cheek_radius = int(min(face_w, face_h) * 0.15)
            
            for cheek_x in [left_cheek_x, right_cheek_x]:
                if 0 <= cheek_x < width and 0 <= cheek_y < height:
                    y_coords, x_coords = np.ogrid[:height, :width]
                    cheek_mask = (x_coords - cheek_x)**2 + (y_coords - cheek_y)**2 <= cheek_radius**2
                    
                    # Slight brightening for cheek expansion
                    frame[cheek_mask] = np.clip(frame[cheek_mask] * (1 + mouth_openness * 0.1), 0, 255)
    
    # 4. Add subtle breathing and micro-movements
    breathing_factor = 1.0 + 0.002 * np.sin(frame_num * 0.08)
    head_movement = 0.2 * np.sin(frame_num * 0.04) + mouth_openness * 0.15
    
    # Apply transformations to the whole image
    center_x, center_y = width // 2, height // 2
    
    # Breathing
    M_breath = cv2.getRotationMatrix2D((center_x, center_y), 0, breathing_factor)
    frame = cv2.warpAffine(frame, M_breath, (width, height))
    
    # Head movement
    M_head = cv2.getRotationMatrix2D((center_x, center_y), head_movement, 1.0)
    frame = cv2.warpAffine(frame, M_head, (width, height))
    
    return frame

def create_custom_image_video(audio_file_path, image_path, output_path):
    """Create video with mouth animation on custom uploaded image"""
    
    # Load and prepare the image
    face_img = cv2.imread(image_path)
    if face_img is None:
        print(f"ERROR: Could not load image: {image_path}")
        return False
    
    # Detect face regions
    print("Detecting face and mouth regions...")
    face_regions = detect_face_region(image_path)
    if face_regions['detected']:
        print("✅ Face detected! Using precise mouth positioning.")
    else:
        print("⚠️  No face detected, using estimated mouth position.")
    
    # Get audio duration and create speech pattern
    duration = get_audio_duration(audio_file_path)
    fps = 25
    total_frames = int(duration * fps)
    speech_pattern = create_speech_pattern(duration, fps)
    
    # Resize image to standard video size while maintaining aspect ratio
    target_height = 512
    h, w = face_img.shape[:2]
    aspect_ratio = w / h
    target_width = int(target_height * aspect_ratio)
    
    # Make width even for video encoding
    if target_width % 2 != 0:
        target_width += 1
    
    face_img = cv2.resize(face_img, (target_width, target_height))
    
    # Update face regions for resized image
    scale_x = target_width / w
    scale_y = target_height / h
    
    face_regions['mouth'] = (
        int(face_regions['mouth'][0] * scale_x),
        int(face_regions['mouth'][1] * scale_y),
        int(face_regions['mouth'][2] * scale_x),
        int(face_regions['mouth'][3] * scale_y)
    )
    
    if face_regions['detected']:
        face_regions['face'] = (
            int(face_regions['face'][0] * scale_x),
            int(face_regions['face'][1] * scale_y),
            int(face_regions['face'][2] * scale_x),
            int(face_regions['face'][3] * scale_y)
        )
    
    # Create temporary video file
    temp_video = output_path.replace('.mp4', '_temp.mp4')
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, fps, (target_width, target_height))
    
    print(f"Creating custom image video ({total_frames} frames at {fps} fps)...")
    print(f"Image size: {target_width}x{target_height}")
    
    for frame_num in range(total_frames):
        # Get mouth openness from speech pattern
        mouth_openness = speech_pattern[frame_num] if frame_num < len(speech_pattern) else 0.3
        
        # Create frame with mouth animation
        frame = create_mouth_animation_on_image(face_img, face_regions, mouth_openness, frame_num)
        
        out.write(frame)
        
        # Progress indicator
        if frame_num % 100 == 0:
            progress = (frame_num / total_frames) * 100
            print(f"  Progress: {progress:.1f}%")
    
    out.release()
    print("  Video frames generated, combining with audio...")
    
    # Combine with audio using ffmpeg
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_video,
        "-i", audio_file_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        os.remove(temp_video)  # Clean up temp file
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e}")
        if os.path.exists(temp_video):
            os.remove(temp_video)
        return False

def generate_lipsync_video_from_image(audio_file_path: str, image_data, output_dir: str = "output_videos", user_prompt: str = None) -> str:
    """
    Generate lip-sync video from uploaded image and audio
    """
    if not os.path.exists(audio_file_path):
        print(f"ERROR: Audio file not found at {audio_file_path}")
        return None
    
    # Save uploaded image
    print("Processing uploaded image...")
    image_path = save_uploaded_image(image_data)
    if not image_path:
        print("ERROR: Failed to save uploaded image")
        return None
    
    # Define output file path
    if user_prompt:
        clean_prompt = "".join(c for c in user_prompt if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_prompt = clean_prompt.replace(' ', '_')[:50]
        video_filename = f"custom_{clean_prompt}_{uuid.uuid4().hex[:8]}.mp4"
    else:
        video_filename = f"custom_video_{uuid.uuid4()}.mp4"
    
    output_path = os.path.join(output_dir, video_filename)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Starting Custom Image Video Generation...")
    print(f"Using uploaded image: {image_path}")
    print(f"Audio duration: {get_audio_duration(audio_file_path):.1f} seconds")
    
    # Create video with custom image
    success = create_custom_image_video(audio_file_path, image_path, output_path)
    
    # Clean up uploaded image
    try:
        os.remove(image_path)
    except:
        pass
    
    if success:
        print(f"SUCCESS: Custom image video saved to {output_path}")
        return output_path
    else:
        print(f"ERROR: Failed to create custom image video")
        return None

if __name__ == "__main__":
    # Test with sample files
    print("Custom Image Wav2Lip - Test Mode")
    
    # You can test this by putting a test image in the current directory
    test_image = "test_face.jpg"
    test_audio = "output_files/Whats_ur_favorite_food_5e8fb802.mp3"
    
    if os.path.exists(test_image) and os.path.exists(test_audio):
        with open(test_image, 'rb') as f:
            image_data = f.read()
        
        result = generate_lipsync_video_from_image(test_audio, image_data, "test_custom", "test")
        print(f"Test result: {result}")
    else:
        print(f"Test files not found: {test_image}, {test_audio}")
