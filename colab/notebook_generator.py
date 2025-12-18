"""Generate customized Colab notebooks for TTS backend."""

import json
import secrets
from pathlib import Path
from typing import Dict, Any


class NotebookGenerator:
    """Generates customized Colab notebooks with model configuration."""
    
    def __init__(self, template_path: str = None):
        """
        Initialize notebook generator.
        
        Args:
            template_path: Path to notebook template file
        """
        if template_path is None:
            template_path = Path(__file__).parent / "notebook_template.ipynb"
        
        self.template_path = Path(template_path)
        
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {self.template_path}")
    
    def generate(
        self,
        backbone_repo: str,
        codec_repo: str,
        device: str = "auto",
        auth_token: str = None
    ) -> tuple[str, str]:
        """
        Generate customized notebook with model configuration.
        
        Args:
            backbone_repo: HuggingFace repo for backbone model
            codec_repo: HuggingFace repo for codec model
            device: Device to use (auto/cuda/cpu)
            auth_token: Authentication token (generated if not provided)
            
        Returns:
            Tuple of (notebook_json_str, auth_token)
        """
        # Generate auth token if not provided
        if auth_token is None:
            auth_token = secrets.token_urlsafe(32)
        
        # Load template
        with open(self.template_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        # Replace placeholders in notebook cells
        replacements = {
            "{{ backbone_repo }}": backbone_repo,
            "{{ codec_repo }}": codec_repo,
            "{{ device }}": device,
            "{{ auth_token }}": auth_token
        }
        
        for cell in notebook.get("cells", []):
            if cell.get("cell_type") == "code":
                source = cell.get("source", [])
                if isinstance(source, list):
                    cell["source"] = [
                        self._replace_placeholders(line, replacements)
                        for line in source
                    ]
                elif isinstance(source, str):
                    cell["source"] = self._replace_placeholders(source, replacements)
        
        # Convert to JSON string
        notebook_json = json.dumps(notebook, indent=1, ensure_ascii=False)
        
        return notebook_json, auth_token
    
    def _replace_placeholders(self, text: str, replacements: Dict[str, str]) -> str:
        """Replace all placeholders in text."""
        for placeholder, value in replacements.items():
            text = text.replace(placeholder, value)
        return text
    
    def generate_to_file(
        self,
        output_path: str,
        backbone_repo: str,
        codec_repo: str,
        device: str = "auto",
        auth_token: str = None
    ) -> str:
        """
        Generate notebook and save to file.
        
        Args:
            output_path: Path to save generated notebook
            backbone_repo: HuggingFace repo for backbone model
            codec_repo: HuggingFace repo for codec model
            device: Device to use (auto/cuda/cpu)
            auth_token: Authentication token (generated if not provided)
            
        Returns:
            Generated auth token
        """
        notebook_json, auth_token = self.generate(
            backbone_repo, codec_repo, device, auth_token
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(notebook_json)
        
        return auth_token
