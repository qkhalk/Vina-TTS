import json
import os
import shutil
from pathlib import Path
from typing import Optional, List
import bcrypt
from auth.models import User


class UserManager:
    """Manages user authentication and CRUD operations with JSON file storage."""
    
    def __init__(self, users_file: str = "config/users.json"):
        self.users_file = Path(users_file)
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()
    
    def _load(self) -> dict:
        """Load users from JSON file."""
        if not self.users_file.exists():
            default_data = {
                "access_enabled": False,
                "users": []
            }
            self._save(default_data)
            return default_data
        
        try:
            with open(self.users_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Validate structure
            if not isinstance(data, dict):
                raise ValueError("Invalid users.json structure")
            if "access_enabled" not in data:
                data["access_enabled"] = False
            if "users" not in data:
                data["users"] = []
                
            return data
        except (json.JSONDecodeError, ValueError) as e:
            # Try to restore from backup
            backup_file = self.users_file.with_suffix(".json.bak")
            if backup_file.exists():
                print(f"⚠️ Corrupted users.json, restoring from backup...")
                shutil.copy(backup_file, self.users_file)
                return self._load()
            
            print(f"❌ Error loading users.json: {e}. Creating new file.")
            default_data = {"access_enabled": False, "users": []}
            self._save(default_data)
            return default_data
    
    def _save(self, data: dict):
        """Save users to JSON file with atomic write and backup."""
        # Create backup
        if self.users_file.exists():
            backup_file = self.users_file.with_suffix(".json.bak")
            shutil.copy(self.users_file, backup_file)
        
        # Atomic write using temp file
        temp_file = self.users_file.with_suffix(".json.tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Replace original file
        temp_file.replace(self.users_file)
    
    def is_access_enabled(self) -> bool:
        """Check if user access protection is enabled."""
        return self._data.get("access_enabled", False)
    
    def set_access_enabled(self, enabled: bool):
        """Enable or disable user access protection."""
        self._data["access_enabled"] = enabled
        self._save(self._data)
    
    def get_all_users(self) -> List[User]:
        """Get all users."""
        return [User.from_dict(u) for u in self._data.get("users", [])]
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user by username."""
        for user_data in self._data.get("users", []):
            if user_data["username"] == username:
                return User.from_dict(user_data)
        return None
    
    def add_user(self, username: str, password: str) -> bool:
        """
        Add new user with bcrypt-hashed password.
        
        Returns:
            True if user added, False if username already exists
        """
        if self.get_user(username):
            return False
        
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user = User(username=username, password_hash=password_hash)
        
        self._data["users"].append(user.to_dict())
        self._save(self._data)
        return True
    
    def remove_user(self, username: str) -> bool:
        """
        Remove user by username.
        
        Returns:
            True if user removed, False if not found
        """
        users = self._data.get("users", [])
        original_count = len(users)
        
        self._data["users"] = [u for u in users if u["username"] != username]
        
        if len(self._data["users"]) < original_count:
            self._save(self._data)
            return True
        return False
    
    def set_user_enabled(self, username: str, enabled: bool) -> bool:
        """
        Enable or disable user.
        
        Returns:
            True if user updated, False if not found
        """
        for user_data in self._data.get("users", []):
            if user_data["username"] == username:
                user_data["enabled"] = enabled
                self._save(self._data)
                return True
        return False
    
    def verify_user(self, username: str, password: str) -> bool:
        """
        Verify user credentials.
        
        Returns:
            True if credentials valid and user enabled, False otherwise
        """
        user = self.get_user(username)
        if not user or not user.enabled:
            return False
        
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                user.password_hash.encode("utf-8")
            )
        except Exception:
            return False
