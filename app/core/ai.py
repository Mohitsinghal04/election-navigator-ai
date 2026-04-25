import os
import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession
try:
    from google.cloud import translate_v2 as translate
except ImportError:
    # Safe fallback for local environments without the SDK
    translate = None
from google.cloud import storage
from typing import Dict, Any, Optional

# Resilient SDK Initializations
translate_client = None
storage_client = None

try:
    if translate:
        translate_client = translate.Client()
    storage_client = storage.Client()
except Exception as e:
    print(f"Cloud SDKs disabled (Local mode): {e}")

def init_vertex() -> None:
    """Official Vertex AI SDK Initialization with safety fallback."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    if project_id:
        try:
            vertexai.init(project=project_id, location=location)
        except Exception as e:
            print(f"Vertex AI not available (Local mode): {e}")

# Call init immediately
init_vertex()

# Define the system instruction to steer the AI specifically towards election topics.
SYSTEM_INSTRUCTION = (
    "You are the Election Navigator AI. Your goal is to help Indian citizens understand "
    "the election process, timelines, and how to register to vote. Be polite, objective, "
    "and clear. Do not express political opinions. Use simple language."
)

class ElectionAssistant:
    """Enterprise-grade assistant leveraging Google Vertex AI and Cloud Translation."""

    def __init__(self) -> None:
        """Initializes the Generative Model with system instructions."""
        self.model = GenerativeModel(
            "gemini-1.5-flash", 
            system_instruction=[SYSTEM_INSTRUCTION]
        )
            
    def get_chat_session(self, history: list = None) -> Optional[ChatSession]:
        """
        Starts a contextual chat session.
        
        Args:
            history (list, optional): Previous chat messages.
            
        Returns:
            Optional[ChatSession]: A Vertex AI chat session or None.
        """
        if self.model:
            return self.model.start_chat(history=history or [])
        return None

    def generate_response(self, query: str, context_history: list = None, language: str = "en") -> Dict[str, Any]:
        """
        Generates a contextual, translated response for the user.
        
        Args:
            query (str): The user's question.
            context_history (list, optional): Previous conversation history.
            language (str): Target language code (e.g., 'hi', 'en').
            
        Returns:
            Dict[str, Any]: A dictionary containing the response, suggestions, and cards.
        """
        try:
            chat = self.get_chat_session(context_history)
            
            # Step 1: Generate AI Response
            response = chat.send_message(query)
            text_out = response.text
            
            # Step 2: Use Cloud Translation if language is not English
            if language != "en" and translate_client:
                 result = translate_client.translate(text_out, target_language=language)
                 text_out = result["translatedText"]
                 
            # Heuristics for suggested actions
            suggestions = ["How to register to vote?", "Show me the timeline."]
            if "voter id" in query.lower():
                suggestions = ["What documents do I need?", "Can I vote without a Voter ID?"]
            elif "timeline" in query.lower():
                return {
                    "response": text_out,
                    "suggested_actions": ["When is the next election?"],
                    "timeline_event": {
                        "title": "General Election Workflow",
                        "steps": ["Notification", "Nominations", "Scrutiny", "Polling", "Counting"]
                    }
                }
                
            return {
                "response": text_out,
                "suggested_actions": suggestions
            }
        except Exception as e:
            print(f"Vertex/Translate Error: {e}")
            return self._fallback_response(query)

    def _fallback_response(self, query: str) -> Dict[str, Any]:
        """Fallback response if cloud services are unavailable."""
        lower_query = query.lower()
        if "timeline" in lower_query or "when" in lower_query or "step" in lower_query:
             text = "The election process in India follows a structured timeline: 1. Gazette Notification, 2. Nomination filing, 3. Scrutiny, 4. Withdrawal of Candidature, 5. Polling, 6. Counting of Votes."
             return {
                "response": text,
                "suggested_actions": ["What is Form 6?", "How to find my booth?"],
                "timeline_event": {
                    "title": "ECI Election Process",
                    "steps": ["Gazette Notification", "Nominations", "Scrutiny", "Polling", "Counting"]
                }
             }
        elif "voter id" in lower_query or "epic" in lower_query:
             text = "A Voter ID, also known as the EPIC (Electors Photo Identity Card), is your primary proof for voting. You can apply via Form 6 on the Voter Service Portal."
             return {
                "response": text,
                "suggested_actions": ["Documents for Form 6", "How to track application?"]
             }
        
        return {
            "response": "Namaste! I am your Election Navigator. I can help you with registration (Form 6), finding your booth, or understanding timelines. Try asking: 'Show me the election timeline'.",
            "suggested_actions": ["Show me the election timeline", "How to register?"]
        }

# Singleton instance
assistant = ElectionAssistant()
