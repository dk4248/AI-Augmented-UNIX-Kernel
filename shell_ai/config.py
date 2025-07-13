"""
Configuration management for Shell AI Assistant
Handles both OpenAI and Ollama configurations
"""

import os
import json
from typing import Dict, Optional
from pathlib import Path

class Config:
    """Configuration manager for Shell AI Assistant"""
    
    # Default configurations
    DEFAULTS = {
        "provider": "openai",
        "openai": {
            "api_key": None,
            "model": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 1000
        },
        "ollama": {
            "host": "http://localhost:11434",
            "model": "deepseek-r1:8b",
            "temperature": 0.1,
            "max_tokens": 1000,
            "available_models": [
                "deepseek-r1:32b",
                "deepseek-r1:8b", 
                "qwen2.5:32b",
                "qwen2.5:7b",
                "qwen3:8b",
                "llama3.1:8b"
            ]
        },
        "history": {
            "max_entries": 20,
            "save_to_file": True,
            "file_path": "~/.shell_ai_history.json"
        },
        "safety": {
            "auto_execute_safe_commands": False,
            "require_confirmation_for_sudo": True,
            "dangerous_patterns": [
                "rm -rf /",
                "dd if=",
                "mkfs",
                "format",
                "> /dev/",
                "chmod -R 777",
                "curl | bash",
                "wget -O- | sh"
            ]
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration"""
        self.config_file = config_file or os.path.expanduser("~/.shell_ai_config.json")
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load configuration from file and environment"""
        # Start with defaults
        config = self.DEFAULTS.copy()
        
        # Load from JSON file if exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    self._deep_merge(config, file_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        # Override with environment variables
        self._load_env_vars(config)
        
        return config
    
    def _deep_merge(self, base: Dict, update: Dict) -> None:
        """Deep merge two dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _load_env_vars(self, config: Dict) -> None:
        """Load configuration from environment variables"""
        # Provider selection
        if os.getenv("SHELL_AI_PROVIDER"):
            config["provider"] = os.getenv("SHELL_AI_PROVIDER")
        
        # OpenAI settings
        if os.getenv("OPENAI_API_KEY"):
            config["openai"]["api_key"] = os.getenv("OPENAI_API_KEY")
        if os.getenv("OPENAI_MODEL"):
            config["openai"]["model"] = os.getenv("OPENAI_MODEL")
        
        # Ollama settings
        if os.getenv("OLLAMA_HOST"):
            config["ollama"]["host"] = os.getenv("OLLAMA_HOST")
        if os.getenv("OLLAMA_MODEL"):
            config["ollama"]["model"] = os.getenv("OLLAMA_MODEL")
    
    def save(self) -> None:
        """Save current configuration to file"""
        try:
            # Don't save sensitive data
            save_config = self.config.copy()
            if "openai" in save_config and "api_key" in save_config["openai"]:
                save_config["openai"]["api_key"] = "***"
            
            with open(self.config_file, 'w') as f:
                json.dump(save_config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value) -> None:
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    @property
    def provider(self) -> str:
        """Get current AI provider"""
        return self.config.get("provider", "openai")
    
    @property
    def is_openai(self) -> bool:
        """Check if using OpenAI"""
        return self.provider == "openai"
    
    @property
    def is_ollama(self) -> bool:
        """Check if using Ollama"""
        return self.provider == "ollama"
    
    @property
    def model(self) -> str:
        """Get current model based on provider"""
        if self.is_openai:
            return self.config["openai"]["model"]
        else:
            return self.config["ollama"]["model"]
    
    @property
    def api_key(self) -> Optional[str]:
        """Get OpenAI API key if using OpenAI"""
        if self.is_openai:
            return self.config["openai"]["api_key"]
        return None
    
    @property
    def ollama_host(self) -> str:
        """Get Ollama host URL"""
        return self.config["ollama"]["host"]
    
    def validate(self) -> bool:
        """Validate current configuration"""
        if self.is_openai:
            if not self.api_key:
                print("Error: OpenAI API key not configured")
                print("Set OPENAI_API_KEY environment variable or run setup.sh")
                return False
        
        elif self.is_ollama:
            # Check if Ollama is accessible
            try:
                import requests
                response = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
                if response.status_code != 200:
                    print(f"Error: Cannot connect to Ollama at {self.ollama_host}")
                    print("Make sure Ollama is running: 'ollama serve'")
                    return False
                
                # Check if model is available
                models = [m["name"] for m in response.json().get("models", [])]
                if self.model not in models:
                    print(f"Error: Model '{self.model}' not found in Ollama")
                    print(f"Available models: {', '.join(models)}")
                    print(f"Pull the model with: 'ollama pull {self.model}'")
                    return False
                    
            except Exception as e:
                print(f"Error: Cannot connect to Ollama: {e}")
                print("Make sure Ollama is installed and running")
                return False
        
        return True