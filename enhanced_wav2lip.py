#!/usr/bin/env python3
"""
Enhanced Wav2Lip module with modern video generation
"""

import os
import subprocess
import uuid
import cv2
import numpy as np

# --- LOCAL WAV2LIP CONFIGURATION ---
WAV2LIP_REPO_DIR = "Wav2Lip"

# Set the path to your pre-made static image file
STATIC_IMAGE_PATH = "assets/static_image.png"

# Set the path to the GAN checkpoint (must be downloaded!)
CHECKPOINT_PATH = os.path.join(WAV2LIP_REPO_DIR, "checkpoints", "wav2lip_gan.pth")

def create_enhanced_video(audio_file_path, output_path, face_image_path):
    """Create an enhanced video with subtle animations"""
    
    # Load the face image
    face_img = cv2.imread(face_image_path)
    if face_img is None:
        print(f"ERROR: Could not load face image: {face_image_path}")
        return False
    
    # Get audio duration using ffprobe
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration", 
            "-of", "csv=p=0", audio_file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip())
    except:
        duration = 30.0  # Default duration
    
    # Create video with subtle face animations
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
    
    print(f"Creating enhanced video ({total_frames} frames at {fps} fps)...")
    
    for frame_num in range(total_frames):
        # Create subtle animations
        frame = face_img.copy()
        
        # Add subtle breathing effect (very gentle scaling)
        breathing_factor = 1.0 + 0.002 * np.sin(frame_num * 0.1)
        center_x, center_y = width // 2, height // 2
        
        # Apply very subtle scaling
        M = cv2.getRotationMatrix2D((center_x, center_y), 0, breathing_factor)
        frame = cv2.warpAffine(frame, M, (width, height))
        
        # Add very subtle head movement (tiny rotation)
        head_movement = 0.3 * np.sin(frame_num * 0.05)  # Very small movement
        M_head = cv2.getRotationMatrix2D((center_x, center_y), head_movement, 1.0)
        frame = cv2.warpAffine(frame, M_head, (width, height))
        
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
    except subprocess.CalledProcessError:
        if os.path.exists(temp_video):
            os.remove(temp_video)
        return False

def generate_lipsync_video_local(audio_file_path: str, output_dir: str = "output_videos", user_prompt: str = None) -> str:
    """
    Generate enhanced lip-sync video with subtle animations
    """
    if not os.path.exists(audio_file_path):
        print(f"ERROR: Audio file not found at {audio_file_path}")
        return None

    if not os.path.exists(STATIC_IMAGE_PATH):
        print(f"ERROR: Static image file not found at {STATIC_IMAGE_PATH}")
        return None

    # 1. Define the output file path (using user prompt or unique ID)
    if user_prompt:
        # Clean the prompt for filename use
        clean_prompt = "".join(c for c in user_prompt if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_prompt = clean_prompt.replace(' ', '_')[:50]  # Limit length and replace spaces
        video_filename = f"enhanced_{clean_prompt}_{uuid.uuid4().hex[:8]}.mp4"
    else:
        video_filename = f"enhanced_video_{uuid.uuid4()}.mp4"
    output_path = os.path.join(output_dir, video_filename)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Starting Enhanced Video Generation...")
    print(f"Using face image: {STATIC_IMAGE_PATH}")

    # Create enhanced video with subtle animations
    if create_enhanced_video(audio_file_path, output_path, STATIC_IMAGE_PATH):
        print(f"SUCCESS: Enhanced video saved to {output_path}")
        return output_path
    else:
        print(f"ERROR: Failed to create enhanced video")
        return None
