#!/usr/bin/env python3
"""
Run Local MCP Server
This script runs the local MCP server
"""

import os
import sys
import asyncio
import logging
import argparse

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from main import main, load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the local MCP server')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    try:
        # Load environment variables from .env file
        if load_dotenv():
            logger.info("Loaded environment variables from .env file")
        else:
            logger.warning("No .env file found or failed to load it")
        
        logger.info("Starting local MCP server...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running local MCP server: {e}")
        sys.exit(1)

# Made with Bob
