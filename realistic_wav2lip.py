#!/usr/bin/env python3
"""
Realistic Wav2Lip alternative with audio-driven mouth animation simulation
"""

import os
import subprocess
import uuid
import cv2
import numpy as np
import librosa

# Configuration
STATIC_IMAGE_PATH = "assets/static_image.png"

def analyze_audio_for_mouth_movement(audio_file_path):
    """Analyze audio to create realistic mouth movement patterns"""
    try:
        # Load audio file
        y, sr = librosa.load(audio_file_path)
        
        # Get audio features for mouth animation
        # RMS energy for overall mouth opening
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        
        # Spectral centroid for mouth shape (higher frequencies = more closed mouth)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        
        # MFCC for more detailed mouth shapes
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        
        # Zero crossing rate for consonant detection
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        
        # Normalize features
        rms = rms / np.max(rms) if np.max(rms) > 0 else rms
        spectral_centroid = spectral_centroid / np.max(spectral_centroid) if np.max(spectral_centroid) > 0 else spectral_centroid
        zcr = zcr / np.max(zcr) if np.max(zcr) > 0 else zcr
        
        return {
            'rms': rms,
            'spectral_centroid': spectral_centroid,
            'mfccs': mfccs,
            'zcr': zcr,
            'duration': len(y) / sr,
            'hop_length': 512,
            'sr': sr
        }
        
    except Exception as e:
        print(f"Warning: Could not analyze audio for mouth movement: {e}")
        return None

def create_mouth_animation_frame(face_img, mouth_openness, mouth_shape, frame_num):
    """Create a frame with simulated mouth movement"""
    frame = face_img.copy()
    height, width = frame.shape[:2]
    
    # Define mouth region (this is a rough approximation - in reality you'd need face detection)
    mouth_center_x = width // 2
    mouth_center_y = int(height * 0.75)  # Mouth is typically in lower 3/4 of face
    
    # Create mouth movement effects
    # 1. Simulate mouth opening by darkening/lightening mouth area
    mouth_radius = int(min(width, height) * 0.03)  # Small mouth region
    
    # Create a mask for the mouth area
    y_coords, x_coords = np.ogrid[:height, :width]
    mouth_mask = (x_coords - mouth_center_x)**2 + (y_coords - mouth_center_y)**2 <= mouth_radius**2
    
    # Apply mouth movement based on audio features
    if mouth_openness > 0.3:  # Speaking/mouth open
        # Darken mouth area to simulate opening
        frame[mouth_mask] = frame[mouth_mask] * (1 - mouth_openness * 0.3)
        
        # Add slight vertical stretch for open mouth
        stretch_factor = 1 + mouth_openness * 0.05
        mouth_region = frame[mouth_center_y-mouth_radius:mouth_center_y+mouth_radius, 
                           mouth_center_x-mouth_radius:mouth_center_x+mouth_radius]
        if mouth_region.size > 0:
            stretched = cv2.resize(mouth_region, 
                                 (mouth_radius*2, int(mouth_radius*2*stretch_factor)))
            if stretched.shape[0] <= mouth_radius*2:
                frame[mouth_center_y-stretched.shape[0]//2:mouth_center_y+stretched.shape[0]//2,
                      mouth_center_x-mouth_radius:mouth_center_x+mouth_radius] = stretched
    
    # 2. Add subtle jaw movement
    jaw_movement = mouth_openness * 2  # Pixel movement
    if jaw_movement > 0.5:
        # Slight downward shift of lower face
        lower_face_start = int(height * 0.6)
        M = np.float32([[1, 0, 0], [0, 1, jaw_movement]])
        frame[lower_face_start:] = cv2.warpAffine(frame[lower_face_start:], M, 
                                                (width, height - lower_face_start))
    
    # 3. Add breathing and micro-movements
    breathing_factor = 1.0 + 0.002 * np.sin(frame_num * 0.1)
    center_x, center_y = width // 2, height // 2
    
    # Apply very subtle scaling
    M = cv2.getRotationMatrix2D((center_x, center_y), 0, breathing_factor)
    frame = cv2.warpAffine(frame, M, (width, height))
    
    # Add very subtle head movement
    head_movement = 0.2 * np.sin(frame_num * 0.05) + mouth_openness * 0.1
    M_head = cv2.getRotationMatrix2D((center_x, center_y), head_movement, 1.0)
    frame = cv2.warpAffine(frame, M_head, (width, height))
    
    return frame

def create_realistic_video(audio_file_path, output_path, face_image_path):
    """Create a realistic video with audio-driven mouth animation"""
    
    # Load the face image
    face_img = cv2.imread(face_image_path)
    if face_img is None:
        print(f"ERROR: Could not load face image: {face_image_path}")
        return False
    
    # Analyze audio for mouth movement
    audio_features = analyze_audio_for_mouth_movement(audio_file_path)
    if audio_features is None:
        print("Warning: Using basic animation without audio analysis")
        duration = 30.0
        rms = None
    else:
        duration = audio_features['duration']
        rms = audio_features['rms']
        spectral_centroid = audio_features['spectral_centroid']
        zcr = audio_features['zcr']
    
    # Create video with audio-driven animations
    fps = 25
    total_frames = int(duration * fps)
    
    # Resize face image to standard size
    height, width = 512, 512
    face_img = cv2.resize(face_img, (width, height))
    
    # Create temporary video file
    temp_video = output_path.replace('.mp4', '_temp.mp4')
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))
    
    print(f"Creating realistic video with audio-driven animation ({total_frames} frames at {fps} fps)...")
    
    for frame_num in range(total_frames):
        if rms is not None:
            # Calculate audio-driven parameters
            # Map frame number to audio feature index
            audio_frame_idx = int((frame_num / total_frames) * len(rms))
            audio_frame_idx = min(audio_frame_idx, len(rms) - 1)
            
            # Get mouth movement parameters from audio
            mouth_openness = rms[audio_frame_idx]
            mouth_shape = spectral_centroid[audio_frame_idx] if audio_frame_idx < len(spectral_centroid) else 0.5
            consonant_strength = zcr[audio_frame_idx] if audio_frame_idx < len(zcr) else 0.5
            
            # Enhance mouth movement for clearer animation
            mouth_openness = np.clip(mouth_openness * 2, 0, 1)  # Amplify mouth opening
            
        else:
            # Basic animation without audio analysis
            mouth_openness = 0.3 + 0.2 * np.sin(frame_num * 0.2)
            mouth_shape = 0.5
        
        # Create frame with mouth animation
        frame = create_mouth_animation_frame(face_img, mouth_openness, mouth_shape, frame_num)
        
        out.write(frame)
    
    out.release()
    
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
    Generate realistic lip-sync video with audio-driven mouth animation
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
        video_filename = f"realistic_{clean_prompt}_{uuid.uuid4().hex[:8]}.mp4"
    else:
        video_filename = f"realistic_video_{uuid.uuid4()}.mp4"
    output_path = os.path.join(output_dir, video_filename)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Starting Realistic Audio-Driven Video Generation...")
    print(f"Using face image: {STATIC_IMAGE_PATH}")
    print(f"Analyzing audio: {audio_file_path}")

    # Create realistic video with audio-driven animations
    if create_realistic_video(audio_file_path, output_path, STATIC_IMAGE_PATH):
        print(f"SUCCESS: Realistic video saved to {output_path}")
        return output_path
    else:
        print(f"ERROR: Failed to create realistic video")
        return None

if __name__ == "__main__":
    # Test with a sample audio file
    test_audio = "output_files/test.mp3"
    if os.path.exists(test_audio):
        result = generate_lipsync_video_local(test_audio, "test_output", "test")
        print(f"Test result: {result}")
    else:
        print("No test audio file found")
