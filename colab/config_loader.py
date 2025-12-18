"""Load and save Colab configuration to config.yaml."""

import os
import yaml
from pathlib import Path
from .config import ColabConfig


def load_colab_config(config_path: str = "config.yaml") -> ColabConfig:
    """
    Load Colab configuration from config.yaml.
    
    Args:
        config_path: Path to config.yaml file
        
    Returns:
        ColabConfig instance
    """
    # Check environment variables first
    env_endpoint = os.getenv("COLAB_ENDPOINT_URL", "")
    env_token = os.getenv("COLAB_AUTH_TOKEN", "")
    
    if env_endpoint and env_token:
        return ColabConfig(
            enabled=True,
            endpoint_url=env_endpoint,
            auth_token=env_token
        )
    
    # Load from config file
    if not Path(config_path).exists():
        return ColabConfig()
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}
    
    colab_data = config.get("colab", {})
    return ColabConfig.from_dict(colab_data)


def save_colab_config(colab_config: ColabConfig, config_path: str = "config.yaml"):
    """
    Save Colab configuration to config.yaml.
    
    Args:
        colab_config: ColabConfig instance
        config_path: Path to config.yaml file
    """
    # Don't save if using environment variables
    if os.getenv("COLAB_ENDPOINT_URL") or os.getenv("COLAB_AUTH_TOKEN"):
        return
    
    # Load existing config
    if Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}
    
    # Update colab section
    config["colab"] = colab_config.to_dict()
    
    # Save back to file
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
