import threading
import torch
import gc
from typing import Optional, Dict, Any
from enum import Enum


class ModelStatus(str, Enum):
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


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
        Get current TTS model instance.
        
        Returns:
            TTS model if loaded, None otherwise
        """
        return self.tts if self.status == ModelStatus.LOADED else None
    
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
