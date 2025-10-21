#!/usr/bin/env python3
"""
Improved Wav2Lip alternative with better mouth animation (no librosa dependency)
"""

import os
import subprocess
import uuid
import cv2
import numpy as np

# Configuration
STATIC_IMAGE_PATH = "assets/static_image.png"

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
        return 30.0  # Default duration

def create_speech_pattern(duration, fps):
    """Create a realistic speech pattern without audio analysis"""
    total_frames = int(duration * fps)
    
    # Create varied speech patterns
    speech_pattern = []
    
    for frame in range(total_frames):
        time = frame / fps
        
        # Base speech rhythm (varies between 2-8 Hz for natural speech)
        base_freq = 4 + 2 * np.sin(time * 0.3)  # Varying frequency
        base_speech = np.sin(time * base_freq * 2 * np.pi)
        
        # Add pauses and emphasis
        pause_pattern = 1.0
        if int(time * 2) % 7 == 0:  # Pause every ~3.5 seconds
            pause_pattern = 0.1
        elif int(time * 3) % 5 == 0:  # Emphasis every ~1.7 seconds
            pause_pattern = 1.5
        
        # Combine patterns
        mouth_openness = np.clip((base_speech + 1) / 2 * pause_pattern, 0, 1)
        
        # Add consonant-like sharp movements
        if frame % 8 == 0:  # Quick consonant movements
            mouth_openness = min(mouth_openness + 0.3, 1.0)
        
        speech_pattern.append(mouth_openness)
    
    return speech_pattern

def create_improved_mouth_frame(face_img, mouth_openness, frame_num):
    """Create a frame with improved mouth movement"""
    frame = face_img.copy()
    height, width = frame.shape[:2]
    
    # Define mouth region (rough approximation)
    mouth_center_x = width // 2
    mouth_center_y = int(height * 0.75)  # Mouth in lower 3/4 of face
    mouth_width = int(width * 0.06)  # Mouth width
    mouth_height = int(height * 0.03)  # Mouth height
    
    # Create mouth animation effects
    if mouth_openness > 0.2:  # Speaking
        # 1. Create mouth opening effect
        mouth_open_height = int(mouth_height * mouth_openness * 2)
        
        # Create elliptical mouth region
        y_coords, x_coords = np.ogrid[:height, :width]
        mouth_mask = ((x_coords - mouth_center_x) / mouth_width)**2 + \
                    ((y_coords - mouth_center_y) / max(mouth_open_height, 1))**2 <= 1
        
        # Darken mouth area to simulate opening
        frame[mouth_mask] = frame[mouth_mask] * (1 - mouth_openness * 0.4)
        
        # 2. Add subtle jaw movement
        jaw_movement = mouth_openness * 1.5  # Pixel movement
        if jaw_movement > 0.3:
            # Slight downward shift of lower face
            lower_face_start = int(height * 0.65)
            if lower_face_start < height - 5:
                M = np.float32([[1, 0, 0], [0, 1, jaw_movement]])
                frame[lower_face_start:] = cv2.warpAffine(
                    frame[lower_face_start:], M, 
                    (width, height - lower_face_start)
                )
        
        # 3. Add cheek movement for strong speech
        if mouth_openness > 0.6:
            # Subtle cheek expansion
            cheek_regions = [
                (int(width * 0.25), int(height * 0.6)),  # Left cheek
                (int(width * 0.75), int(height * 0.6))   # Right cheek
            ]
            
            for cheek_x, cheek_y in cheek_regions:
                cheek_radius = int(min(width, height) * 0.08)
                y_coords, x_coords = np.ogrid[:height, :width]
                cheek_mask = (x_coords - cheek_x)**2 + (y_coords - cheek_y)**2 <= cheek_radius**2
                
                # Slight brightening for cheek expansion
                frame[cheek_mask] = np.clip(frame[cheek_mask] * (1 + mouth_openness * 0.1), 0, 255)
    
    # 4. Add natural micro-movements
    # Breathing
    breathing_factor = 1.0 + 0.003 * np.sin(frame_num * 0.08)
    
    # Head movement correlated with speech
    head_movement = 0.3 * np.sin(frame_num * 0.04) + mouth_openness * 0.2
    
    # Apply transformations
    center_x, center_y = width // 2, height // 2
    
    # Breathing
    M_breath = cv2.getRotationMatrix2D((center_x, center_y), 0, breathing_factor)
    frame = cv2.warpAffine(frame, M_breath, (width, height))
    
    # Head movement
    M_head = cv2.getRotationMatrix2D((center_x, center_y), head_movement, 1.0)
    frame = cv2.warpAffine(frame, M_head, (width, height))
    
    return frame

def create_improved_video(audio_file_path, output_path, face_image_path):
    """Create an improved video with realistic mouth animation"""
    
    # Load the face image
    face_img = cv2.imread(face_image_path)
    if face_img is None:
        print(f"ERROR: Could not load face image: {face_image_path}")
        return False
    
    # Get audio duration
    duration = get_audio_duration(audio_file_path)
    
    # Create video parameters
    fps = 25
    total_frames = int(duration * fps)
    
    # Resize face image to standard size
    height, width = 512, 512
    face_img = cv2.resize(face_img, (width, height))
    
    # Generate speech pattern
    speech_pattern = create_speech_pattern(duration, fps)
    
    # Create temporary video file
    temp_video = output_path.replace('.mp4', '_temp.mp4')
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))
    
    print(f"Creating improved video with realistic speech patterns ({total_frames} frames at {fps} fps)...")
    
    for frame_num in range(total_frames):
        # Get mouth openness from speech pattern
        mouth_openness = speech_pattern[frame_num] if frame_num < len(speech_pattern) else 0.3
        
        # Create frame with improved mouth animation
        frame = create_improved_mouth_frame(face_img, mouth_openness, frame_num)
        
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

def generate_lipsync_video_local(audio_file_path: str, output_dir: str = "output_videos", user_prompt: str = None) -> str:
    """
    Generate improved lip-sync video with realistic mouth animation patterns
    """
    if not os.path.exists(audio_file_path):
        print(f"ERROR: Audio file not found at {audio_file_path}")
        return None

    if not os.path.exists(STATIC_IMAGE_PATH):
        print(f"ERROR: Static image file not found at {STATIC_IMAGE_PATH}")
        return None

    # Define the output file path
    if user_prompt:
        clean_prompt = "".join(c for c in user_prompt if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_prompt = clean_prompt.replace(' ', '_')[:50]
        video_filename = f"improved_{clean_prompt}_{uuid.uuid4().hex[:8]}.mp4"
    else:
        video_filename = f"improved_video_{uuid.uuid4()}.mp4"
    output_path = os.path.join(output_dir, video_filename)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Starting Improved Video Generation with Realistic Speech Patterns...")
    print(f"Using face image: {STATIC_IMAGE_PATH}")
    print(f"Audio duration: {get_audio_duration(audio_file_path):.1f} seconds")

    # Create improved video
    if create_improved_video(audio_file_path, output_path, STATIC_IMAGE_PATH):
        print(f"SUCCESS: Improved video saved to {output_path}")
        return output_path
    else:
        print(f"ERROR: Failed to create improved video")
        return None

if __name__ == "__main__":
    # Test with a sample audio file
    test_audio = "output_files/Whats_ur_favorite_food_5e8fb802.mp3"
    if os.path.exists(test_audio):
        result = generate_lipsync_video_local(test_audio, "test_output", "test_improved")
        print(f"Test result: {result}")
    else:
        print("No test audio file found")
