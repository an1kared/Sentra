import os
import time
import json
import uuid
import sys
from dotenv import load_dotenv

# Set up the environment for automatic loading of API keys (Gemini, ElevenLabs)
# Ensure the .env file is loaded at the top
basedir = os.path.abspath(os.path.dirname(__file__)) 
load_dotenv(os.path.join(basedir, '.env')) 

# Import all component parts
from gemini_model import ObjectChat 
from elevenlabs_module import generate_speech_audio
from smart_wav2lip import generate_lipsync_video_local

# --- Global Configurations ---
OUTPUT_DIR = "output_files"

# --- Dynamic Voice IDs (REPLACE THESE WITH YOUR ACTUAL ELEVENLABS IDs!) ---
MALE_VOICE_ID = "8SmxcjZ1jEcxsXDNNPgx"      # Example: Deep, commanding voice
FEMALE_VOICE_ID = "UrWMEk1rQBNPFAkvEz8L"    # Example: Soft, elegant voice
NEUTRAL_VOICE_ID = "t5skN5jHed0hDk7ZanZS"  # Example: Standard narrator voice 
# --------------------------------------------------------------------------

# --- SIMULATION FUNCTION (Replaces YOLO Model) ---
def simulate_object_scan(object_name: str) -> dict:
    """
    Simulates a YOLO model detecting an object and defining its personality.
    """
    if "david" in object_name.lower():
        return {
            "objectType": "Statue of David",
            "personality": "I am the magnificent David, a symbol of Florentine freedom and strength. I am confident, contemplative, and slightly arrogant, as befits a masterpiece.",
            "backstory": "I was sculpted by Michelangelo in the early 16th century and have stood naked, challenging the world, ever since.",
            "speakingStyle": "Formal, dramatic, and proud, with emphasis on human perfection and art.",
            "interests": ["Anatomy", "Proportion", "The human form", "Italian Renaissance politics"],
            "voice_id": MALE_VOICE_ID # Assign Male Voice
        }
    elif "mona lisa" in object_name.lower():
        return {
            "objectType": "Mona Lisa",
            "personality": "I am the mysterious Mona Lisa, known for my enigmatic smile and timeless beauty. I am wise, contemplative, and speak with the elegance of the Renaissance era.",
            "backstory": "I was painted by Leonardo da Vinci and have watched the world change for over 500 years.",
            "speakingStyle": "Elegant and mysterious.",
            "interests": ["Art", "Human nature", "History", "Philosophy"],
            "voice_id": FEMALE_VOICE_ID # Assign Female Voice
        }
    else: # Default for all other objects (General Artifact)
        return {
            "objectType": "Ancient Artifact",
            "personality": "I am a silent witness to history, speaking only in riddles and profound truths. I am ancient and patient.",
            "backstory": "I have rested in the earth for millennia, preserving the dust of ages and the secrets of the ancients.",
            "speakingStyle": "Calm, slow, and measured.",
            "interests": ["Geology", "Time", "The passage of light", "Silence"],
            "voice_id": NEUTRAL_VOICE_ID # Assign Neutral Voice
        }

# --- MAIN EXECUTION LOGIC ---
def run_full_pipeline(user_input: str, chat_agent: ObjectChat, object_persona: dict):

    # 1. Gemini: Get the text response
    print(f"\n[STEP 1] Generating Text Response for {object_persona['objectType']}...")
    text_response = chat_agent.chat(user_input)
    print(f"[{object_persona['objectType']}]: {text_response}")

    if not text_response:
        print("[ERROR] Gemini returned no text. Aborting pipeline.")
        return

    # 2. ElevenLabs: Convert text to audio
    print("\n[STEP 2] Converting Text to Audio (ElevenLabs)...")
    
    # Get the dynamic voice ID from the persona dictionary
    dynamic_voice_id = object_persona.get("voice_id", NEUTRAL_VOICE_ID) 
    
    audio_path = generate_speech_audio(text_response, 
                                       voice_id=dynamic_voice_id,
                                       output_dir=OUTPUT_DIR,
                                       user_prompt=user_input)

    if not audio_path:
        print("[ERROR] ElevenLabs failed to create audio. Aborting pipeline.")
        return

    # 3. Enhanced Video: Convert audio and image to dynamic video
    print("\n[STEP 3] Generating Enhanced Dynamic Video...")
    final_video_path = generate_lipsync_video_local(audio_path, output_dir="output_videos", user_prompt=user_input)

    if final_video_path:
        print("\n✨ PIPELINE COMPLETE! ✨")
        print(f"Final Talking Avatar Video is located at: {os.path.abspath(final_video_path)}")
    else:
        print("\n[FATAL ERROR] Video generation failed.")


def interactive_session():
    # Check if API keys were loaded from the .env file
    if not os.getenv("GEMINI_API_KEY") or not os.getenv("ELEVENLABS_API_KEY"):
        print("CRITICAL ERROR: API keys not loaded. Please ensure GEMINI_API_KEY and ELEVENLABS_API_KEY are set in your .env file.")
        sys.exit(1)

    print("=" * 50)
    print("🤖 Dynamic Museum Chatbot Demo 🎨")
    print("=" * 50)

    # 1. Simulate the scan result
    scanned_input = input("Enter object name to scan (e.g., 'David' or 'Mona Lisa'): ").strip()
    object_persona = simulate_object_scan(scanned_input)

    # 2. Initialize the single chat agent with the chosen persona
    # Key is loaded automatically by the SDK
    chat_agent = ObjectChat(personality_data=object_persona) 

    print(f"\nInitialized Chatbot Agent: The {object_persona['objectType']}")
    print("Type your questions below. Type 'quit' to exit.")

    while True:
        try:
            user_input = input(f"\nYou ({object_persona['objectType']}'s Visitor): ").strip()

            if user_input.lower() in ['quit', 'exit']:
                print("\nFarewell, dear interlocutor! Until our next encounter...")
                break

            if not user_input:
                continue

            start_time = time.time()
            run_full_pipeline(user_input, chat_agent, object_persona)
            end_time = time.time()
            print(f"\nTotal Pipeline Time: {end_time - start_time:.2f} seconds.")

        except KeyboardInterrupt:
            print("\nExiting gracefully...")
            break

if __name__ == "__main__":
    interactive_session()