import threading
import torch
import gc
from typing import Optional, Dict, Any, List
from enum import Enum


# Voice compatibility for GGUF quantized models
# These 4 voices are optimized for GGUF models (q4/q8) based on testing
GGUF_OPTIMIZED_VOICES = [
    "Vĩnh (nam miền Nam)",
    "Bình (nam miền Bắc)",
    "Ngọc (nữ miền Bắc)",
    "Dung (nữ miền Nam)",
]


class ModelStatus(str, Enum):
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


class BackendMode(str, Enum):
    LOCAL = "local"
    REMOTE = "remote"


class ModelManager:
    """Singleton manager for TTS model lifecycle."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        if ModelManager._instance is not None:
            raise RuntimeError("Use ModelManager.get_instance() instead")
        
        self.tts = None
        self.status = ModelStatus.UNLOADED
        self.error_message = ""
        self.config = {}
        self.using_lmdeploy = False
        self._model_lock = threading.Lock()
        
        # Colab backend support
        self._backend_mode = BackendMode.LOCAL
        self._colab_client = None
        self._colab_endpoint = ""
        self._colab_token = ""
        self._colab_connected = False
    
    @classmethod
    def get_instance(cls) -> "ModelManager":
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def get_status(self) -> Dict[str, Any]:
        """Get current model status and info."""
        status_info = {
            "status": self.status,
            "error": self.error_message,
            "config": self.config.copy(),
            "backend": "LMDeploy" if self.using_lmdeploy else "Standard",
            "backend_mode": self._backend_mode.value,
            "colab_connected": self._colab_connected,
            "colab_endpoint": self._colab_endpoint if self._colab_connected else "",
            "supported_voices": self.get_supported_voices(),
        }
        
        if torch.cuda.is_available() and self.status == ModelStatus.LOADED:
            try:
                status_info["gpu_memory_allocated"] = torch.cuda.memory_allocated() / 1024**3
                status_info["gpu_memory_reserved"] = torch.cuda.memory_reserved() / 1024**3
            except Exception:
                pass
        
        return status_info
    
    def load_model(
        self,
        backbone_repo: str,
        codec_repo: str,
        backbone_device: str,
        codec_device: str,
        enable_triton: bool = True,
        max_batch_size: int = 8,
    ) -> Dict[str, Any]:
        """
        Load TTS model with specified configuration.
        
        Returns:
            Status dict with success/error info
        """
        with self._model_lock:
            if self.status == ModelStatus.LOADED:
                return {
                    "success": True,
                    "message": "Model already loaded",
                    "status": self.get_status()
                }
            
            if self.status == ModelStatus.LOADING:
                return {
                    "success": False,
                    "message": "Model is currently loading",
                    "status": self.get_status()
                }
            
            self.status = ModelStatus.LOADING
            self.error_message = ""
            self.config = {
                "backbone_repo": backbone_repo,
                "codec_repo": codec_repo,
                "backbone_device": backbone_device,
                "codec_device": codec_device,
                "enable_triton": enable_triton,
                "max_batch_size": max_batch_size,
            }
            
            try:
                # Determine if we should use LMDeploy
                use_lmdeploy = self._should_use_lmdeploy(backbone_repo, backbone_device)
                
                if use_lmdeploy:
                    self.tts = self._load_fast_model(
                        backbone_repo, codec_repo, backbone_device, codec_device,
                        enable_triton, max_batch_size
                    )
                    self.using_lmdeploy = True
                else:
                    self.tts = self._load_standard_model(
                        backbone_repo, codec_repo, backbone_device, codec_device
                    )
                    self.using_lmdeploy = False
                
                self.status = ModelStatus.LOADED
                return {
                    "success": True,
                    "message": f"Model loaded successfully ({'LMDeploy' if self.using_lmdeploy else 'Standard'} backend)",
                    "status": self.get_status()
                }
                
            except Exception as e:
                self.status = ModelStatus.ERROR
                self.error_message = str(e)
                self.tts = None
                return {
                    "success": False,
                    "message": f"Failed to load model: {str(e)}",
                    "status": self.get_status()
                }
    
    def unload_model(self) -> Dict[str, Any]:
        """
        Unload current model and free memory.
        
        Returns:
            Status dict with success/error info
        """
        with self._model_lock:
            if self.status == ModelStatus.UNLOADED:
                return {
                    "success": True,
                    "message": "Model already unloaded",
                    "status": self.get_status()
                }
            
            try:
                if self.tts is not None:
                    # Cleanup model-specific resources
                    if self.using_lmdeploy and hasattr(self.tts, 'cleanup_memory'):
                        self.tts.cleanup_memory()
                    
                    del self.tts
                    self.tts = None
                
                # Aggressive memory cleanup
                self._cleanup_memory()
                
                self.status = ModelStatus.UNLOADED
                self.error_message = ""
                self.using_lmdeploy = False
                
                return {
                    "success": True,
                    "message": "Model unloaded successfully",
                    "status": self.get_status()
                }
                
            except Exception as e:
                self.status = ModelStatus.ERROR
                self.error_message = str(e)
                return {
                    "success": False,
                    "message": f"Failed to unload model: {str(e)}",
                    "status": self.get_status()
                }
    
    def restart_model(self) -> Dict[str, Any]:
        """
        Restart model with current configuration.
        
        Returns:
            Status dict with success/error info
        """
        with self._model_lock:
            if not self.config:
                return {
                    "success": False,
                    "message": "No model configuration available. Please load a model first.",
                    "status": self.get_status()
                }
            
            # Store config before unload
            config = self.config.copy()
            
            # Unload (without lock since we're already in lock)
            if self.tts is not None:
                try:
                    if self.using_lmdeploy and hasattr(self.tts, 'cleanup_memory'):
                        self.tts.cleanup_memory()
                    del self.tts
                    self.tts = None
                    self._cleanup_memory()
                except Exception as e:
                    print(f"Warning during unload in restart: {e}")
            
            # Reload with saved config
            self.status = ModelStatus.LOADING
            self.error_message = ""
            
            try:
                use_lmdeploy = self._should_use_lmdeploy(
                    config["backbone_repo"],
                    config["backbone_device"]
                )
                
                if use_lmdeploy:
                    self.tts = self._load_fast_model(
                        config["backbone_repo"],
                        config["codec_repo"],
                        config["backbone_device"],
                        config["codec_device"],
                        config.get("enable_triton", True),
                        config.get("max_batch_size", 8),
                    )
                    self.using_lmdeploy = True
                else:
                    self.tts = self._load_standard_model(
                        config["backbone_repo"],
                        config["codec_repo"],
                        config["backbone_device"],
                        config["codec_device"],
                    )
                    self.using_lmdeploy = False
                
                self.status = ModelStatus.LOADED
                return {
                    "success": True,
                    "message": "Model restarted successfully",
                    "status": self.get_status()
                }
                
            except Exception as e:
                self.status = ModelStatus.ERROR
                self.error_message = str(e)
                self.tts = None
                return {
                    "success": False,
                    "message": f"Failed to restart model: {str(e)}",
                    "status": self.get_status()
                }
    
    def get_model(self):
        """
        Get current TTS model instance based on active backend mode.
        
        Returns:
            TTS model (local) or ColabTTSClient (remote), None if not available
        """
        if self._backend_mode == BackendMode.REMOTE:
            return self._colab_client if self._colab_connected else None
        else:
            return self.tts if self.status == ModelStatus.LOADED else None
    
    def get_supported_voices(self, all_voices: Optional[List[str]] = None) -> List[str]:
        """
        Get list of supported voice names based on current model configuration.
        
        GGUF backbone models are optimized for only 4 voices, regardless of codec.
        Non-GGUF models support all voices.
        
        Args:
            all_voices: List of all available voice names. If None, returns filtered list hint.
        
        Returns:
            List of supported voice names
        """
        # If no model is loaded, return all voices (or empty list if none provided)
        if self.status != ModelStatus.LOADED or not self.config:
            return all_voices if all_voices is not None else []
        
        backbone_repo = self.config.get("backbone_repo", "")
        
        # Filter based on backbone type only (codec is irrelevant)
        if "gguf" in backbone_repo.lower():
            # GGUF models: only show optimized voices
            if all_voices is not None:
                return [v for v in GGUF_OPTIMIZED_VOICES if v in all_voices]
            else:
                return GGUF_OPTIMIZED_VOICES
        else:
            # Non-GGUF models: show all voices
            return all_voices if all_voices is not None else []
    
    def _should_use_lmdeploy(self, backbone_repo: str, device: str) -> bool:
        """Determine if LMDeploy should be used."""
        if "gguf" in backbone_repo.lower():
            return False
        
        if device.lower() == "auto":
            return torch.cuda.is_available()
        elif device.lower() in ["cuda", "gpu"]:
            return torch.cuda.is_available()
        else:
            return False
    
    def _load_fast_model(
        self, backbone_repo, codec_repo, backbone_device, codec_device,
        enable_triton, max_batch_size
    ):
        """Load model with FastVieNeuTTS (LMDeploy backend)."""
        from vieneu_tts import FastVieNeuTTS
        
        # Determine codec device
        if "ONNX" in codec_repo or "onnx" in codec_repo:
            codec_device = "cpu"
        elif backbone_device.lower() in ["cuda", "gpu"]:
            codec_device = "cuda"
        
        tts = FastVieNeuTTS(
            backbone_repo=backbone_repo,
            backbone_device="cuda",
            codec_repo=codec_repo,
            codec_device=codec_device,
            memory_util=0.3,
            tp=1,
            enable_prefix_caching=True,
            enable_triton=enable_triton,
            max_batch_size=max_batch_size,
        )
        
        return tts
    
    def _load_standard_model(
        self, backbone_repo, codec_repo, backbone_device, codec_device
    ):
        """Load model with VieNeuTTS (standard backend)."""
        from vieneu_tts import VieNeuTTS
        
        # Adjust device names for GGUF
        if "gguf" in backbone_repo.lower() and backbone_device.lower() == "cuda":
            backbone_device = "gpu"
        
        # Determine codec device
        if "ONNX" in codec_repo or "onnx" in codec_repo:
            codec_device = "cpu"
        elif backbone_device.lower() == "auto":
            codec_device = "cuda" if torch.cuda.is_available() else "cpu"
        
        tts = VieNeuTTS(
            backbone_repo=backbone_repo,
            backbone_device=backbone_device,
            codec_repo=codec_repo,
            codec_device=codec_device,
        )
        
        return tts
    
    def _cleanup_memory(self):
        """Aggressive memory cleanup."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        gc.collect()
    
    # Colab Backend Management
    
    @property
    def backend_mode(self) -> BackendMode:
        """Get current backend mode."""
        return self._backend_mode
    
    @backend_mode.setter
    def backend_mode(self, mode: BackendMode):
        """Set backend mode."""
        if isinstance(mode, str):
            mode = BackendMode(mode)
        self._backend_mode = mode
    
    def set_colab_connection(self, endpoint_url: str, auth_token: str) -> Dict[str, Any]:
        """
        Configure Colab backend connection.
        
        Args:
            endpoint_url: Colab ngrok URL
            auth_token: Authentication token
            
        Returns:
            Status dict with success/error info
        """
        try:
            from colab.client import ColabTTSClient
            
            # Test connection
            test_client = ColabTTSClient(endpoint_url, auth_token, timeout=10)
            success, message, latency = test_client.test_connection()
            
            if not success:
                return {
                    "success": False,
                    "message": f"Connection test failed: {message}",
                }
            
            # Connection successful, save client
            self._colab_client = test_client
            self._colab_endpoint = endpoint_url
            self._colab_token = auth_token
            self._colab_connected = True
            
            return {
                "success": True,
                "message": f"Connected successfully (latency: {latency:.0f}ms)",
                "latency_ms": latency
            }
            
        except Exception as e:
            self._colab_connected = False
            return {
                "success": False,
                "message": f"Failed to connect: {str(e)}"
            }
    
    def disconnect_colab(self) -> Dict[str, Any]:
        """
        Disconnect from Colab backend.
        
        Returns:
            Status dict with success/error info
        """
        try:
            if self._colab_client:
                del self._colab_client
                self._colab_client = None
            
            self._colab_endpoint = ""
            self._colab_token = ""
            self._colab_connected = False
            
            # Switch to local mode if was using remote
            if self._backend_mode == BackendMode.REMOTE:
                self._backend_mode = BackendMode.LOCAL
            
            return {
                "success": True,
                "message": "Disconnected from Colab successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to disconnect: {str(e)}"
            }
    
    def check_colab_health(self) -> Dict[str, Any]:
        """
        Check Colab backend health.
        
        Returns:
            Health status dict
        """
        if not self._colab_connected or not self._colab_client:
            return {
                "connected": False,
                "message": "Not connected to Colab"
            }
        
        try:
            health = self._colab_client.health_check()
            return {
                "connected": True,
                "health": health,
                "message": "Colab backend is healthy"
            }
        except Exception as e:
            return {
                "connected": False,
                "message": f"Health check failed: {str(e)}"
            }
    
    def get_active_backend_status(self) -> Dict[str, Any]:
        """
        Get status of active backend for UI display.
        
        Returns:
            Status dict with backend info
        """
        if self._backend_mode == BackendMode.REMOTE:
            if self._colab_connected:
                health = self.check_colab_health()
                return {
                    "mode": "remote",
                    "status": "connected" if health.get("connected") else "disconnected",
                    "endpoint": self._colab_endpoint,
                    "health": health.get("health", {})
                }
            else:
                return {
                    "mode": "remote",
                    "status": "not_configured",
                    "message": "Colab backend not connected"
                }
        else:
            return {
                "mode": "local",
                "status": self.status.value,
                "model_loaded": self.status == ModelStatus.LOADED,
                "backend": "LMDeploy" if self.using_lmdeploy else "Standard"
            }
