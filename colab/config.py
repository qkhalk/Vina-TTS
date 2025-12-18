"""Colab configuration management."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ColabConfig:
    """Configuration for Google Colab backend connection."""
    
    enabled: bool = False
    endpoint_url: str = ""
    auth_token: str = ""
    timeout_seconds: int = 60
    health_check_interval: int = 30
    
    def is_valid(self) -> bool:
        """Check if configuration is valid for connection."""
        return bool(self.endpoint_url and self.auth_token)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ColabConfig":
        """Create ColabConfig from dictionary."""
        return cls(
            enabled=data.get("enabled", False),
            endpoint_url=data.get("endpoint_url", ""),
            auth_token=data.get("auth_token", ""),
            timeout_seconds=data.get("timeout_seconds", 60),
            health_check_interval=data.get("health_check_interval", 30),
        )
    
    def to_dict(self) -> dict:
        """Convert ColabConfig to dictionary."""
        return {
            "enabled": self.enabled,
            "endpoint_url": self.endpoint_url,
            "auth_token": self.auth_token,
            "timeout_seconds": self.timeout_seconds,
            "health_check_interval": self.health_check_interval,
        }
