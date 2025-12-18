"""HTTP client for Google Colab TTS backend."""

import base64
import time
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ColabTTSClient:
    """HTTP client that proxies TTS requests to Google Colab runtime."""
    
    def __init__(self, endpoint_url: str, auth_token: str, timeout: int = 60):
        """
        Initialize Colab TTS client.
        
        Args:
            endpoint_url: Base URL of Colab FastAPI server (e.g., https://abc123.ngrok.io)
            auth_token: Bearer token for authentication
            timeout: Request timeout in seconds
        """
        self.endpoint_url = endpoint_url.rstrip("/")
        self.auth_token = auth_token
        self.timeout = timeout
        
        # Setup session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        })
    
    def synthesize(
        self,
        text: str,
        voice_sample_path: str,
        voice_transcript: str,
        speed: float = 1.0,
        watermark: bool = True
    ) -> Optional[bytes]:
        """
        Synthesize speech using Colab backend.
        
        Args:
            text: Text to synthesize
            voice_sample_path: Path to voice sample audio
            voice_transcript: Transcript of voice sample
            speed: Speech speed multiplier
            watermark: Whether to add audio watermark
            
        Returns:
            Audio data as bytes, or None if request fails
        """
        try:
            payload = {
                "text": text,
                "voice_sample_path": voice_sample_path,
                "voice_transcript": voice_transcript,
                "speed": speed,
                "watermark": watermark
            }
            
            response = self.session.post(
                f"{self.endpoint_url}/tts/synthesize",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            audio_base64 = data.get("audio_base64", "")
            audio_bytes = base64.b64decode(audio_base64)
            
            return audio_bytes
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Colab request timed out after {self.timeout}s")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Colab request failed: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to decode Colab response: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check Colab backend health status.
        
        Returns:
            Health status dict with model_loaded, gpu_memory_used_gb, uptime_seconds
        """
        try:
            response = self.session.get(
                f"{self.endpoint_url}/health",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "model_loaded": False
            }
    
    def test_connection(self) -> tuple[bool, str, Optional[float]]:
        """
        Test connection to Colab backend.
        
        Returns:
            Tuple of (success, message, latency_ms)
        """
        try:
            start_time = time.time()
            health = self.health_check()
            latency_ms = (time.time() - start_time) * 1000
            
            if health.get("status") == "ok":
                return True, "Connection successful", latency_ms
            else:
                error_msg = health.get("error", "Unknown error")
                return False, f"Health check failed: {error_msg}", latency_ms
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}", None
    
    def __del__(self):
        """Cleanup session on deletion."""
        if hasattr(self, 'session'):
            self.session.close()
