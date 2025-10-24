"""
Utility functions for the MCP server

This module contains utility functions used across the MCP server implementation.
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure logging with the specified log level
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        logger.warning(f"Invalid log level: {log_level}, using INFO")
        numeric_level = logging.INFO
        
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    logger.info(f"Logging configured with level: {log_level}")

def get_env_file_path(env_file: Optional[str] = None) -> str:
    """
    Get the path to the environment file
    
    Args:
        env_file: Optional path to the environment file
        
    Returns:
        Path to the environment file
    """
    if env_file and os.path.exists(env_file):
        return env_file
        
    # Check for .env in the current directory
    if os.path.exists('.env'):
        return '.env'
        
    # Check for .env in the parent directory
    parent_env = os.path.join('..', '.env')
    if os.path.exists(parent_env):
        return parent_env
        
    # Default to .env in the current directory even if it doesn't exist
    return '.env'

# Made with Bob
