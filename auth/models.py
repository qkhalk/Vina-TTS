from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


@dataclass
class User:
    username: str
    password_hash: str
    enabled: bool = True
    created_at: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "enabled": self.enabled,
            "created_at": self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            username=data["username"],
            password_hash=data["password_hash"],
            enabled=data.get("enabled", True),
            created_at=data.get("created_at"),
        )
