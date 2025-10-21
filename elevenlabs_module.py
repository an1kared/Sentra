import os
import uuid
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings
import os # Ensure os is imported

# --- Configuration: Explicit Path Loading ---
basedir = os.path.abspath(os.path.dirname(__file__)) 
load_dotenv(os.path.join(basedir, '.env')) 
# ---------------------------------------------

# Correctly retrieves the key from the environment variable
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Instantiate the ElevenLabs client
try:
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
except Exception as e:
    print(f"Error initializing ElevenLabs client: {e}. Check your .env file and API key.")
    client = None

def generate_speech_audio(text_response: str, voice_id: str, output_dir: str = "output_files", user_prompt: str = None) -> str:
    """
    Converts a text string to an MP3 file using ElevenLabs with a dynamic voice ID.
    """
    if not client:
        return None

    # 1. Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # 2. Define the output file path (using user prompt or unique ID)
    if user_prompt:
        # Clean the prompt for filename use
        clean_prompt = "".join(c for c in user_prompt if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_prompt = clean_prompt.replace(' ', '_')[:50]  # Limit length and replace spaces
        audio_filename = f"{clean_prompt}_{uuid.uuid4().hex[:8]}.mp3"
    else:
        audio_filename = f"{uuid.uuid4()}.mp3"
    output_path = os.path.join(output_dir, audio_filename)

    # --- ElevenLabs API Call ---
    # The voice_id is now taken directly from the function argument!
    model_id = "eleven_turbo_v2_5"      

    print(f"Generating speech with Voice ID: {voice_id}...") 

    try:
        audio_stream = client.text_to_speech.convert(
            text=text_response,
            voice_id=voice_id, # <<< CRITICAL: Uses the dynamic ID passed from main_pipeline
            model_id=model_id,
            output_format="mp3_44100_128",
        )

        # 3. Save the audio stream to a file
        with open(output_path, "wb") as f:
            for chunk in audio_stream:
                if chunk:
                    f.write(chunk)

        print(f"SUCCESS: Audio saved to {output_path}")
        return output_path

    except Exception as e:
        print(f"ERROR during ElevenLabs generation: {e}")
        return None