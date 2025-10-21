# gemini_model.py (FINAL FIX for Models.GenerativeModel AttributeError)

# Import the correct Google Generative AI module
import google.generativeai as genai
import time
import os
from dotenv import load_dotenv

# Set up environment variables to be available to the client
load_dotenv()

class ObjectChat:
    """A chatbot initialized with a dynamic museum object personality."""

    def __init__(self, personality_data: dict):
        # Configure the API key for google.generativeai
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables")
        
        genai.configure(api_key=api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        self.conversation_history = []
        self.personality = personality_data

    def chat(self, user_message: str) -> str:
        """Send a message to the persona and get a response"""

        # --- Context Builder ---
        personality_context = f"""You are a historic object with the following persona:

Object Type: {self.personality['objectType']}
Personality: {self.personality['personality']}
Backstory: {self.personality['backstory']}
Speaking Style: {self.personality['speakingStyle']}
Interests: {', '.join(self.personality['interests'])}

Stay strictly true to this personality in all your responses. Keep responses conversational and under 100 words. Do not break character or mention that you are an AI, a large language model, or software. You are the object brought to life."""

        # Add conversation history for context
        history_text = ""
        for user_msg, ai_msg in self.conversation_history[-3:]: # Keep last 3 exchanges
            history_text += f"\nHuman: {user_msg}\n{self.personality['objectType']}: {ai_msg}"

        prompt = f"{personality_context}{history_text}\n\nHuman: {user_message}\n{self.personality['objectType']}:"

        try:
            # Generate content using the configured model
            response = self.model.generate_content(prompt)
            
            response_text = response.text.strip()

            # Store in conversation history
            self.conversation_history.append((user_message, response_text))

            return response_text
        except Exception as e:
            print(f"Error in chat: {e}")
            return "I find myself lost in contemplation... Perhaps you could rephrase your question?"
