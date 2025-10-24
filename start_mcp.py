#!/usr/bin/env python3
"""
Run Local MCP Server

This script runs the local MCP server for IBM OpenPages integration.
It handles command line arguments, environment configuration, and server startup.
"""

import os
import sys
import asyncio
import logging
import argparse
from typing import Optional, NoReturn

# Import from the current directory structure
# This ensures the script works regardless of where it's executed from
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from server_runner import main
from utils import configure_logging, get_env_file_path
from settings import settings, create_settings

# Version information
__version__ = "1.0.0"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description=f'OpenPages Local MCP Server v{__version__}'
    )
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--port', type=int, help='Server port (overrides .env setting)')
    parser.add_argument('--host', type=str, help='Server host (overrides .env setting)')
    parser.add_argument('--env-file', type=str, default='.env',
                        help='Path to environment file (default: .env)')
    parser.add_argument('--version', action='version',
                        version=f'%(prog)s {__version__}')
    
    return parser.parse_args()


def main_cli() -> Optional[NoReturn]:
    """Main entry point for the CLI.
    
    Returns:
        Optional[NoReturn]: Returns None on success, or exits with error code
    """
    args = parse_arguments()
    
    try:
        # Get the environment file path
        env_file = get_env_file_path(args.env_file)
        logger.info(f"Using environment file: {env_file}")
        
        # Create settings with the specified environment file
        app_settings = create_settings(env_file)
        
        # Set debug mode if requested via command line
        if args.debug:
            app_settings.DEBUG = True
            configure_logging("DEBUG")
            logger.debug("Debug mode enabled via command line")
        else:
            configure_logging(app_settings.LOG_LEVEL)
        
        # Override settings with command line arguments if provided
        if args.port:
            app_settings.PORT = args.port
            logger.info(f"Using port from command line: {args.port}")
        
        if args.host:
            app_settings.HOST = args.host
            logger.info(f"Using host from command line: {args.host}")
        
        logger.info(f"Starting OpenPages Local MCP Server v{__version__}...")
        logger.info(f"Server will listen on {app_settings.HOST}:{app_settings.PORT}")
        
        # Pass only the settings object to the main function
        asyncio.run(main(custom_settings=app_settings))
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running local MCP server: {e}")
        if args.debug:
            import traceback
            logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main_cli()
