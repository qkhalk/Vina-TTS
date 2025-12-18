"""Google Colab integration module for remote TTS backend."""

from .client import ColabTTSClient
from .config import ColabConfig
from .notebook_generator import NotebookGenerator
from .config_loader import load_colab_config, save_colab_config

__all__ = [
    "ColabTTSClient",
    "ColabConfig",
    "NotebookGenerator",
    "load_colab_config",
    "save_colab_config",
]
