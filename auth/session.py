import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from auth.models import UserRole


class SessionManager:
    """Manages user and admin sessions."""
    
    def __init__(self, session_timeout_hours: int = 24):
        self._sessions: Dict[str, dict] = {}
        self.session_timeout = timedelta(hours=session_timeout_hours)
    
    def create_session(self, username: str, role: UserRole) -> str:
        """
        Create new session for user or admin.
        
        Returns:
            Session token
        """
        token = secrets.token_urlsafe(32)
        self._sessions[token] = {
            "username": username,
            "role": role,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
        }
        return token
    
    def validate_session(self, token: str) -> Optional[dict]:
        """
        Validate session token and return session data.
        
        Returns:
            Session data if valid, None if invalid or expired
        """
        if token not in self._sessions:
            return None
        
        session = self._sessions[token]
        now = datetime.utcnow()
        
        # Check expiry
        if now - session["created_at"] > self.session_timeout:
            self.invalidate_session(token)
            return None
        
        # Update last activity
        session["last_activity"] = now
        return session
    
    def invalidate_session(self, token: str):
        """Invalidate session by token."""
        if token in self._sessions:
            del self._sessions[token]
    
    def invalidate_user_sessions(self, username: str):
        """Invalidate all sessions for a user."""
        tokens_to_remove = [
            token for token, session in self._sessions.items()
            if session["username"] == username
        ]
        for token in tokens_to_remove:
            del self._sessions[token]
    
    def get_role(self, token: str) -> Optional[UserRole]:
        """Get role for session token."""
        session = self.validate_session(token)
        return session["role"] if session else None
    
    def cleanup_expired(self):
        """Remove expired sessions."""
        now = datetime.utcnow()
        expired = [
            token for token, session in self._sessions.items()
            if now - session["created_at"] > self.session_timeout
        ]
        for token in expired:
            del self._sessions[token]
