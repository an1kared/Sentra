#!/usr/bin/env python3
"""
Smart Wav2Lip module that tries real Wav2Lip first, falls back to enhanced version
"""

import os
import sys
import subprocess
import uuid

# Configuration
WAV2LIP_REPO_DIR = "Wav2Lip"
STATIC_IMAGE_PATH = "assets/static_image.png"
CHECKPOINT_PATH = os.path.join(WAV2LIP_REPO_DIR, "checkpoints", "wav2lip_gan.pth")

def test_wav2lip_environment():
    """Test if Wav2Lip can run without errors"""
    try:
        # Test if we can import the required modules without the np.complex error
        original_dir = os.getcwd()
        os.chdir(WAV2LIP_REPO_DIR)
        
        # Try to run a quick test
        cmd = [sys.executable, "-c", "import audio, models.wav2lip; print('Wav2Lip environment OK')"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        os.chdir(original_dir)
        
        if result.returncode == 0:
            print("✅ Real Wav2Lip environment is working!")
            return True
        else:
            print("❌ Real Wav2Lip has dependency issues:", result.stderr.strip())
            return False
            
    except Exception as e:
        if 'original_dir' in locals():
            os.chdir(original_dir)
        print(f"❌ Cannot test Wav2Lip environment: {e}")
        return False

def generate_with_real_wav2lip(audio_file_path: str, output_dir: str, user_prompt: str = None) -> str:
    """Try to generate video using real Wav2Lip"""
    
    if not os.path.exists(audio_file_path):
        print(f"ERROR: Audio file not found at {audio_file_path}")
        return None

    if not os.path.exists(STATIC_IMAGE_PATH):
        print(f"ERROR: Static image file not found at {STATIC_IMAGE_PATH}")
        return None

    if not os.path.exists(CHECKPOINT_PATH):
        print("ERROR: Wav2Lip checkpoint not found. Did you download wav2lip_gan.pth?")
        return None

    # Define output path
    if user_prompt:
        clean_prompt = "".join(c for c in user_prompt if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_prompt = clean_prompt.replace(' ', '_')[:50]
        video_filename = f"wav2lip_{clean_prompt}_{uuid.uuid4().hex[:8]}.mp4"
    else:
        video_filename = f"wav2lip_video_{uuid.uuid4()}.mp4"
    
    output_path = os.path.join(output_dir, video_filename)
    os.makedirs(output_dir, exist_ok=True)

    # Construct command with absolute paths
    abs_checkpoint = os.path.abspath(CHECKPOINT_PATH)
    abs_face = os.path.abspath(STATIC_IMAGE_PATH)
    abs_audio = os.path.abspath(audio_file_path)
    abs_output = os.path.abspath(output_path)
    
    command = [
        sys.executable, "inference.py",
        "--checkpoint_path", abs_checkpoint,
        "--face", abs_face,
        "--audio", abs_audio,
        "--outfile", abs_output,
        "--resize_factor", "1",
        "--pads", "0", "10", "0", "0" 
    ]

    print(f"🎬 Attempting REAL Wav2Lip generation...")
    print(f"Working directory: {os.path.abspath(WAV2LIP_REPO_DIR)}")

    try:
        original_dir = os.getcwd()
        os.chdir(WAV2LIP_REPO_DIR)
        
        # Run with timeout to prevent hanging
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        
        os.chdir(original_dir)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: Real Wav2Lip video saved to {output_path}")
            return output_path
        else:
            print(f"❌ Real Wav2Lip failed: {result.stderr.strip()}")
            return None

    except subprocess.TimeoutExpired:
        os.chdir(original_dir)
        print("❌ Real Wav2Lip timed out")
        return None
    except Exception as e:
        if 'original_dir' in locals():
            os.chdir(original_dir)
        print(f"❌ Real Wav2Lip error: {e}")
        return None

def generate_with_enhanced_wav2lip(audio_file_path: str, output_dir: str, user_prompt: str = None) -> str:
    """Fallback to enhanced video generation"""
    try:
        # Try improved version first (realistic speech patterns, no librosa dependency)
        from improved_wav2lip import generate_lipsync_video_local as improved_generate
        print("🎭 Using Improved Speech Pattern Animation (realistic mouth movements)")
        return improved_generate(audio_file_path, output_dir, user_prompt)
    except Exception as e:
        print(f"⚠️  Improved version failed: {e}")
        try:
            # Fallback to basic enhanced version
            from enhanced_wav2lip import generate_lipsync_video_local as enhanced_generate
            print("🎭 Falling back to Basic Enhanced Wav2Lip (template + animations)")
            return enhanced_generate(audio_file_path, output_dir, user_prompt)
        except Exception as e2:
            print(f"❌ All enhanced versions failed: {e2}")
            return None

def generate_lipsync_video_local(audio_file_path: str, output_dir: str = "output_videos", user_prompt: str = None) -> str:
    """
    Smart video generation: Try real Wav2Lip first, fallback to enhanced version
    """
    print("\n🤖 Smart Wav2Lip: Determining best generation method...")
    
    # Check if all required files exist
    if not os.path.exists(audio_file_path):
        print(f"ERROR: Audio file not found at {audio_file_path}")
        return None

    if not os.path.exists(STATIC_IMAGE_PATH):
        print(f"ERROR: Static image file not found at {STATIC_IMAGE_PATH}")
        return None

    # First, test if real Wav2Lip environment is working
    if test_wav2lip_environment() and os.path.exists(CHECKPOINT_PATH):
        print("🎬 Attempting Real Wav2Lip (actual lip-sync)...")
        result = generate_with_real_wav2lip(audio_file_path, output_dir, user_prompt)
        
        if result:
            return result
        else:
            print("⚠️  Real Wav2Lip failed, falling back to Enhanced version...")
    else:
        print("⚠️  Real Wav2Lip environment not ready, using Enhanced version...")

    # Fallback to enhanced version
    return generate_with_enhanced_wav2lip(audio_file_path, output_dir, user_prompt)

if __name__ == "__main__":
    # Test the environment
    print("Testing Smart Wav2Lip environment...")
    test_wav2lip_environment()
