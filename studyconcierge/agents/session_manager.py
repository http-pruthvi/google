"""
Session Manager Agent for StudyConcierge
"""
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

class InMemorySessionService:
    """Simple in-memory session storage"""
    
    def __init__(self):
        self.sessions = {}
    
    def create_session(self, user_id: str) -> str:
        """Creates a new session for a user"""
        session_id = f"session_{user_id}_{int(datetime.now().timestamp())}"
        self.sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "data": {}
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves session data"""
        if session_id in self.sessions:
            self.sessions[session_id]["last_accessed"] = datetime.now().isoformat()
            return self.sessions[session_id]
        return None
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Updates session data"""
        if session_id in self.sessions:
            self.sessions[session_id]["data"].update(data)
            self.sessions[session_id]["last_accessed"] = datetime.now().isoformat()
            return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Deletes a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

class SessionManagerAgent:
    def __init__(self, session_service=None, memory_bank=None, use_adk: bool = False, adk_model: Optional[str] = None):
        self.session_service = session_service or InMemorySessionService()
        self.memory_bank = memory_bank
        self.current_session_id = None
        self.use_adk = use_adk
        self.adk_model = adk_model
        
    def start_session(self, user_id: str) -> str:
        """
        Starts a new session for the user.
        
        Args:
            user_id (str): Unique identifier for the user
            
        Returns:
            str: Session ID
        """
        logger.info(f"Starting new session for user: {user_id}")
        self.current_session_id = self.session_service.create_session(user_id)
        
        # Log session start in memory
        if self.memory_bank:
            session_data = {
                "session_id": self.current_session_id,
                "user_id": user_id,
                "event": "session_started",
                "timestamp": datetime.now().isoformat()
            }
            self.memory_bank.save("session_events", session_data)
            
        return self.current_session_id
    
    def get_session_data(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves current session data.
        
        Returns:
            Optional[Dict[str, Any]]: Session data or None if no active session
        """
        if not self.current_session_id:
            return None
            
        return self.session_service.get_session(self.current_session_id)
    
    def update_session_progress(self, progress_data: Dict[str, Any]) -> bool:
        """
        Updates session with progress data.
        
        Args:
            progress_data (Dict[str, Any]): Progress information to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.current_session_id:
            logger.warning("No active session to update")
            return False
            
        logger.info("Updating session progress")
        
        # Update session data
        success = self.session_service.update_session(self.current_session_id, {
            "progress": progress_data,
            "last_updated": datetime.now().isoformat()
        })
        
        # Log progress update in memory
        if success and self.memory_bank:
            progress_event = {
                "session_id": self.current_session_id,
                "event": "progress_updated",
                "data": progress_data,
                "timestamp": datetime.now().isoformat()
            }
            self.memory_bank.save("session_events", progress_event)
            
        return success
    
    def end_session(self) -> bool:
        """
        Ends the current session.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.current_session_id:
            logger.warning("No active session to end")
            return False
            
        logger.info(f"Ending session: {self.current_session_id}")

        # Optional ADK summary
        summary_text = None
        try:
            if self.use_adk:
                current_data = self.get_session_data()
                summary_text = self._summarize_session_with_adk(current_data or {})
        except Exception as e:
            logger.debug(f"ADK session summary failed: {e}")
        
        # Log session end in memory
        if self.memory_bank:
            session_end_data = {
                "session_id": self.current_session_id,
                "event": "session_ended",
                "timestamp": datetime.now().isoformat()
            }
            self.memory_bank.save("session_events", session_end_data)
            if summary_text:
                try:
                    self.memory_bank.save("session_summary", {
                        "session_id": self.current_session_id,
                        "summary": summary_text,
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception:
                    pass
            
        # Delete session
        success = self.session_service.delete_session(self.current_session_id)
        self.current_session_id = None
        
        return success
    
    def get_user_history(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves user history from sessions.
        
        Args:
            user_id (str): User identifier
            
        Returns:
            Dict[str, Any]: User history data
        """
        logger.info(f"Retrieving history for user: {user_id}")
        
        # In a real implementation, this would query all sessions for the user
        # For now, we'll return a simple structure
        history = {
            "user_id": user_id,
            "sessions_count": 0,
            "total_study_time": 0,
            "completed_tasks": [],
            "preferred_topics": []
        }
        
        # If we have memory bank, try to retrieve historical data
        if self.memory_bank:
            session_events = self.memory_bank.retrieve("session_events")
            if session_events:
                history["sessions_count"] = len([e for e in session_events if e.get("user_id") == user_id and e.get("event") == "session_started"])
                
        return history

    def _summarize_session_with_adk(self, session_data: Dict[str, Any]) -> Optional[str]:
        """Use ADK to summarize a session's data into a short paragraph."""
        try:
            from studyconcierge.adk_agent import build_session_adk_agent
        except Exception:
            return None
        agent = build_session_adk_agent(memory_bank=self.memory_bank, model=self.adk_model)
        if agent is None:
            return None
        prompt = (
            "Summarize the following session data in a concise paragraph highlighting progress and next steps.\n"
            f"Session Data JSON: {json.dumps(session_data)[:2000]}\n"
        )
        for method in ("run", "ask", "call", "generate"):
            fn = getattr(agent, method, None)
            if not callable(fn):
                continue
            try:
                result = fn(prompt)
                if asyncio.iscoroutine(result):
                    result = asyncio.get_event_loop().run_until_complete(result)
                if isinstance(result, str):
                    return result
                try:
                    return json.dumps(result)
                except Exception:
                    continue
            except Exception:
                continue
        return None