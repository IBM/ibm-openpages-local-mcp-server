"""
Configuration settings for the GRC MCP Server
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # Application settings
    APP_NAME: str = "GRC MCP Server"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Server mode settings
    SERVER_MODE: str = os.getenv("SERVER_MODE", "remote")  # 'remote' or 'local'
    
    # OpenPages settings
    _base_url: str = os.getenv("OPENPAGES_BASE_URL", "")
    # Ensure the base URL has the correct protocol
    OPENPAGES_BASE_URL: str = (_base_url if not _base_url or
                              _base_url.startswith('http://') or
                              _base_url.startswith('https://')
                              else f"https://{_base_url}")
    OPENPAGES_AUTHENTICATION_TYPE: str = os.getenv("OPENPAGES_AUTHENTICATION_TYPE", "basic")
    OPENPAGES_USERNAME: str = os.getenv("OPENPAGES_USERNAME", "")
    OPENPAGES_PASSWORD: str = os.getenv("OPENPAGES_PASSWORD", "")
    OPENPAGES_APIKEY: str = os.getenv("OPENPAGES_APIKEY", "")
    OPENPAGES_AUTHENTICATION_URL: str = os.getenv("OPENPAGES_AUTHENTICATION_URL", "")

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # SSL settings
    SSL_VERIFY: bool = os.getenv("SSL_VERIFY", "True").lower() == "true"
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

# Create settings instance
settings = Settings()

# Made with Bob
