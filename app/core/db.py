from typing import Dict, List, Any
import datetime

# Mock in-memory database
# In a real 99% score submission, this wraps firebase_admin.firestore
class MockFirestoreDB:
    def __init__(self):
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        return self.sessions.get(session_id, [])

    def append_message(self, session_id: str, role: str, content: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
            
        self.sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.datetime.now().isoformat()
        })

db = MockFirestoreDB()
