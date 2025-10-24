"""
Configuration settings for the GRC MCP Server
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Dict, Any

class Settings(BaseSettings):
    """Application settings"""
    
    # Application settings
    APP_NAME: str = "GRC MCP Server"
    DEBUG: bool = False
    
    # Server mode settings
    SERVER_MODE: str = "local"  # 'remote' or 'local'
    
    # OpenPages settings
    _base_url: str = ""
    # Ensure the base URL has the correct protocol
    OPENPAGES_BASE_URL: str = ""
    OPENPAGES_AUTHENTICATION_TYPE: str = "basic"
    OPENPAGES_USERNAME: str = ""
    OPENPAGES_PASSWORD: str = ""
    OPENPAGES_APIKEY: str = ""
    OPENPAGES_AUTHENTICATION_URL: str = ""

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # SSL settings
    SSL_VERIFY: bool = True
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    def __init__(self, env_file: Optional[str] = None, **data: Any):
        """
        Initialize settings with optional custom environment file
        
        Args:
            env_file: Optional path to environment file
            data: Additional data to initialize settings with
        """
        # Set custom env file if provided
        if env_file:
            self.model_config["env_file"] = env_file
            
        super().__init__(**data)
        
        # Process base URL to ensure it has the correct protocol
        if self._base_url:
            if not (self._base_url.startswith('http://') or self._base_url.startswith('https://')):
                self.OPENPAGES_BASE_URL = f"https://{self._base_url}"
            else:
                self.OPENPAGES_BASE_URL = self._base_url

# Create settings instance with default .env file
settings = Settings()

# Function to create settings with custom env file
def create_settings(env_file: str) -> Settings:
    """
    Create settings instance with custom environment file
    
    Args:
        env_file: Path to environment file
        
    Returns:
        Settings instance with values from the specified environment file
    """
    return Settings(env_file=env_file)

# Made with Bob
