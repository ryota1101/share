"""
Configuration loader for Multi-LLM Chat
Loads and validates model configurations from YAML files
"""

import os
import yaml
import logging
from typing import Dict, List, Optional

class ConfigLoader:
    """Configuration loader for AI models"""
    
    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Default config path
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'models.yaml')
        
        self.config_path = os.path.abspath(config_path)
        self._config = None
        
        # Load configuration
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            if not os.path.exists(self.config_path):
                self.logger.error(f"Configuration file not found: {self.config_path}")
                self._config = {'models': [], 'providers': {}}
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._config = yaml.safe_load(file)
            
            # Validate configuration structure
            if not isinstance(self._config, dict):
                raise ValueError("Configuration must be a dictionary")
            
            if 'models' not in self._config:
                self._config['models'] = []
            
            if 'providers' not in self._config:
                self._config['providers'] = {}
            
            self.logger.info(f"Loaded configuration from {self.config_path}")
            self.logger.info(f"Found {len(self._config['models'])} models")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self._config = {'models': [], 'providers': {}}
    
    def reload_config(self):
        """Reload configuration from file"""
        self.logger.info("Reloading configuration")
        self._load_config()
    
    def get_models(self) -> List[Dict]:
        """Get all configured models"""
        if not self._config:
            return []
        
        return self._config.get('models', [])
    
    def get_model(self, model_name: str) -> Optional[Dict]:
        """Get specific model configuration"""
        models = self.get_models()
        
        for model in models:
            if model.get('name') == model_name:
                return model
        
        return None
    
    def get_providers(self) -> Dict:
        """Get provider configurations"""
        if not self._config:
            return {}
        
        return self._config.get('providers', {})
    
    def get_provider(self, provider_name: str) -> Optional[Dict]:
        """Get specific provider configuration"""
        providers = self.get_providers()
        return providers.get(provider_name)
    
    def get_models_by_provider(self, provider_name: str) -> List[Dict]:
        """Get all models for a specific provider"""
        models = self.get_models()
        return [model for model in models if model.get('provider') == provider_name]
    
    def get_models_with_capability(self, capability: str) -> List[Dict]:
        """Get all models that support a specific capability"""
        models = self.get_models()
        result = []
        
        for model in models:
            capabilities = model.get('capabilities', {})
            if capabilities.get(capability, False):
                result.append(model)
        
        return result
    
    def validate_model_config(self, model_config: Dict) -> tuple:
        """
        Validate model configuration
        Returns (is_valid: bool, errors: List[str])
        """
        errors = []
        required_fields = ['name', 'provider', 'model_id']
        
        # Check required fields
        for field in required_fields:
            if field not in model_config:
                errors.append(f"Missing required field: {field}")
        
        # Validate capabilities structure
        if 'capabilities' in model_config:
            capabilities = model_config['capabilities']
            if not isinstance(capabilities, dict):
                errors.append("Capabilities must be a dictionary")
            else:
                valid_capabilities = ['text_input', 'image_input', 'image_output', 'streaming']
                for cap in capabilities:
                    if cap not in valid_capabilities:
                        errors.append(f"Unknown capability: {cap}")
        
        # Validate settings structure
        if 'settings' in model_config:
            settings = model_config['settings']
            if not isinstance(settings, dict):
                errors.append("Settings must be a dictionary")
        
        return len(errors) == 0, errors
    
    def get_environment_variables(self) -> Dict[str, str]:
        """Get required environment variables for all providers"""
        providers = self.get_providers()
        env_vars = {}
        
        for provider_name, provider_config in providers.items():
            for key, env_var in provider_config.items():
                if key.endswith('_env'):
                    actual_key = key.replace('_env', '')
                    env_value = os.getenv(env_var)
                    env_vars[f"{provider_name}_{actual_key}"] = env_value
        
        return env_vars
    
    def check_environment_setup(self) -> Dict[str, bool]:
        """Check if all required environment variables are set"""
        providers = self.get_providers()
        status = {}
        
        for provider_name, provider_config in providers.items():
            provider_status = True
            
            for key, env_var in provider_config.items():
                if key.endswith('_env'):
                    if not os.getenv(env_var):
                        provider_status = False
                        self.logger.warning(f"Missing environment variable: {env_var}")
            
            status[provider_name] = provider_status
        
        return status