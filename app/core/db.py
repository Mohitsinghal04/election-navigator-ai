"""
Database module for Election Navigator AI.
"""
import datetime
import os
from typing import Any, Dict, List

from google.cloud import firestore

class Database:
    """Production-grade asynchronous database handler for Election Navigator AI."""

    def __init__(self) -> None:
        self.collection = "sessions"
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        try:
            self.db_client = firestore.AsyncClient(project=self.project_id) if self.project_id else None
        except OSError as e:
            print(f"Firestore disabled (Local mode): {e}")
            self.db_client = None

    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the chat history for a given session.

        Args:
            session_id (str): The unique session identifier.

        Returns:
            List[Dict[str, Any]]: A list of message objects.
        """
        if not self.db_client:
            return []
        try:
            doc_ref = self.db_client.collection(self.collection).document(session_id)
            doc = await doc_ref.get()
            if doc.exists:
                return doc.to_dict().get("messages", [])
        except OSError:
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
        if not self.db_client:
            return
        try:
            doc_ref = self.db_client.collection(self.collection).document(session_id)
            new_msg = {
                "role": role,
                "content": content,
                "timestamp": datetime.datetime.now().isoformat(),
            }
            await doc_ref.set({"messages": firestore.ArrayUnion([new_msg])}, merge=True)
        except OSError:
            pass


db = Database()
