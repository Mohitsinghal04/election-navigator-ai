import os
import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession
from typing import Dict, Any

# Mock state if Vertex AI is not fully configured locally
_IS_MOCKED = True

def init_vertex() -> None:
    global _IS_MOCKED
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    if project_id and project_id != "your-project-id":
        try:
            vertexai.init(project=project_id, location=location)
            _IS_MOCKED = False
        except Exception as e:
            print(f"Failed to initialize Vertex AI: {e}")

# Call init immediately
init_vertex()

# Define the system instruction to steer the AI specifically towards election topics.
SYSTEM_INSTRUCTION = (
    "You are the Election Navigator AI. Your goal is to help Indian citizens understand "
    "the election process, timelines, and how to register to vote. Be polite, objective, "
    "and clear. Do not express political opinions. Use simple language."
)

class ElectionAssistant:
    def __init__(self):
        self.model = None
        if not _IS_MOCKED:
            self.model = GenerativeModel(
                "gemini-1.5-flash", # Maximum compatibility
                system_instruction=[SYSTEM_INSTRUCTION]
            )
            
    def get_chat_session(self, history: list = None) -> ChatSession:
        if self.model:
            return self.model.start_chat(history=history or [])
        return None

    def generate_response(self, query: str, context_history: list = None, language: str = "en") -> Dict[str, Any]:
        """Generates a response using Vertex AI Gemini."""
        if _IS_MOCKED:
            return self._mock_response(query)
            
        try:
            chat = self.get_chat_session(context_history)
            
            # If target language is not English, instruct it to translate.
            prompt = query
            if language != "en":
                 prompt += f" (Please respond in language code: {language})"
                 
            response = chat.send_message(prompt)
            
            # Extremely simplified heuristics for suggested actions
            suggestions = ["How to register to vote?", "Show me the timeline."]
            if "voter id" in query.lower():
                suggestions = ["What documents do I need?", "Can I vote without a Voter ID?"]
                
            return {
                "response": response.text,
                "suggested_actions": suggestions
            }
        except Exception as e:
            print(f"Vertex Error: {e}")
            return {
                "response": "I apologize, but I am currently facing technical difficulties connecting to my knowledge base.",
                "suggested_actions": ["Try again later"]
            }

    def _mock_response(self, query: str) -> Dict[str, Any]:
        """Mock response for local development without credentials."""
        lower_query = query.lower()
        if "voter id" in lower_query:
             text = "A Voter ID (EPIC) is issued by the Election Commission of India. It serves as identity proof for casting your vote."
             actions = ["How to apply for Voter ID?", "Documents needed"]
        elif "timeline" in lower_query:
             text = "The general election timeline includes: 1. Notification, 2. Filing Nominations, 3. Scrutiny, 4. Withdrawal, 5. Campaigning, 6. Polling, 7. Counting."
             actions = ["When is the next election?"]
             return {
                "response": text,
                "suggested_actions": actions,
                "timeline_event": {
                    "title": "General Election Workflow",
                    "steps": ["Notification", "Nominations", "Scrutiny", "Polling", "Counting"]
                }
             }
        else:
             text = "I am the Election Navigator. I can assist you with understanding voter registration, finding your polling booth, and election timelines."
             actions = ["What is a Voter ID?", "Show me the election timeline.", "How to register to vote?"]
             
        return {
            "response": text,
            "suggested_actions": actions
        }

# Singleton instance
assistant = ElectionAssistant()
