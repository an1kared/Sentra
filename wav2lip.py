import os
import subprocess
import uuid

# --- LOCAL WAV2LIP CONFIGURATION ---
WAV2LIP_REPO_DIR = "Wav2Lip"

# Set the path to your pre-made static image file
STATIC_IMAGE_PATH = "assets/static_image.png"

# Set the path to the GAN checkpoint (must be downloaded!)
CHECKPOINT_PATH = os.path.join(WAV2LIP_REPO_DIR, "checkpoints", "wav2lip_gan.pth")

def generate_lipsync_video_local(audio_file_path: str, output_dir: str = "output_videos", user_prompt: str = None) -> str:
    """
    Runs the Wav2Lip inference script locally using the command line.
    """
    if not os.path.exists(audio_file_path):
        print(f"ERROR: Audio file not found at {audio_file_path}")
        return None

    if not os.path.exists(STATIC_IMAGE_PATH):
        print(f"ERROR: Static image file not found at {STATIC_IMAGE_PATH}")
        return None

    if not os.path.exists(CHECKPOINT_PATH):
        print("ERROR: Wav2Lip checkpoint not found. Did you download wav2lip_gan.pth?")
        return None

    # 1. Define the output file path (using user prompt or unique ID)
    if user_prompt:
        # Clean the prompt for filename use
        clean_prompt = "".join(c for c in user_prompt if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_prompt = clean_prompt.replace(' ', '_')[:50]  # Limit length and replace spaces
        video_filename = f"{clean_prompt}_{uuid.uuid4().hex[:8]}.mp4"
    else:
        video_filename = f"video_{uuid.uuid4()}.mp4"
    output_path = os.path.join(output_dir, video_filename)
    os.makedirs(output_dir, exist_ok=True)

    # 2. Construct the Wav2Lip command with absolute paths
    abs_checkpoint = os.path.abspath(CHECKPOINT_PATH)
    abs_face = os.path.abspath(STATIC_IMAGE_PATH)
    abs_audio = os.path.abspath(audio_file_path)
    abs_output = os.path.abspath(output_path)
    
    command = [
        "python3", "inference.py",
        "--checkpoint_path", abs_checkpoint,
        "--face", abs_face,
        "--audio", abs_audio,
        "--outfile", abs_output,
        "--resize_factor", "1",
        "--pads", "0", "10", "0", "0" 
    ]

    print(f"Starting Wav2Lip generation...")
    print(f"Working directory: {os.path.abspath(WAV2LIP_REPO_DIR)}")

    # 3. Execute the command from within the Wav2Lip directory
    try:
        # Change to Wav2Lip directory and run the command
        original_dir = os.getcwd()
        os.chdir(WAV2LIP_REPO_DIR)
        subprocess.run(command, check=True)
        os.chdir(original_dir)
        print(f"SUCCESS: Video saved to {output_path}")
        return output_path

    except subprocess.CalledProcessError as e:
        print(f"FATAL ERROR during Wav2Lip execution. Check the command and dependencies: {e}")
        return None
    except FileNotFoundError:
        print("CRITICAL ERROR: 'python' or 'ffmpeg' not found. Check your system PATH.")
        return None