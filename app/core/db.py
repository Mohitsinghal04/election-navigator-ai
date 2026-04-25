from typing import Dict, List, Any
import datetime
import os
import datetime
from typing import List, Dict, Any, Optional
from google.cloud import firestore

# Initialize Async Firestore Client with safety fallback
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
try:
    db_client = firestore.AsyncClient(project=project_id) if project_id else None
except Exception as e:
    print(f"Firestore disabled (Local mode): {e}")
    db_client = None

class Database:
    """Production-grade asynchronous database handler for Election Navigator AI."""

    def __init__(self):
        self.collection = "sessions"

    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the chat history for a given session.
        
        Args:
            session_id (str): The unique session identifier.
            
        Returns:
            List[Dict[str, Any]]: A list of message objects.
        """
        if not db_client:
            return []
        try:
            doc_ref = db_client.collection(self.collection).document(session_id)
            doc = await doc_ref.get()
            if doc.exists:
                return doc.to_dict().get("messages", [])
        except Exception as e:
            # Fallback for logging would go here
            pass
        return []

    async def append_message(self, session_id: str, role: str, content: str) -> None:
        """
        Appends a new message to the session history in Firestore.
        
        Args:
            session_id (str): The unique session identifier.
            role (str): The role of the sender (user/model).
            content (str): The message content.
        """
        if not db_client:
            return
        try:
            doc_ref = db_client.collection(self.collection).document(session_id)
            new_msg = {
                "role": role, 
                "content": content, 
                "timestamp": datetime.datetime.now().isoformat()
            }
            await doc_ref.set({
                "messages": firestore.ArrayUnion([new_msg])
            }, merge=True)
        except Exception:
            pass

db = Database()
