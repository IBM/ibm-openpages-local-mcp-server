"""
Base Tool for OpenPages MCP Server
Provides common functionality for all tool classes
"""

import logging
from typing import Any, Dict, List, Optional

from mcp.types import TextContent  # type: ignore
from openpages_client import OpenPagesClient

# Configure logging
logger = logging.getLogger(__name__)

class BaseTool:
    """
    Base class for OpenPages tools
    
    This class provides common functionality for all tool classes,
    including field mapping, type definition handling, and response formatting.
    """
    
    def __init__(self, client: OpenPagesClient):
        """
        Initialize base tool
        
        Args:
            client: OpenPages API client
        """
        self.client = client
        
    async def get_type_definition(self, object_type: str) -> Dict[str, Any]:
        """
        Get type definition from OpenPages
        
        Args:
            object_type: Type of object (e.g., "SOXIssue", "SOXControl")
            
        Returns:
            Dict containing the type definition
            
        Raises:
            Exception: If the type definition cannot be retrieved
        """
        try:
            logger.info(f"Fetching type definition for: {object_type}")
            type_info = await self.client.get_type_definition(object_type)
            
            if not type_info or "field_definitions" not in type_info:
                logger.warning(f"No field definitions found for {object_type}")
                raise ValueError(f"No field definitions found for {object_type}")
                
            return type_info
        except Exception as e:
            logger.error(f"Error getting type definition: {e}")
            raise
            
    def create_field_mapping(self, field_definitions: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Create a mapping of field names to their SQL column names
        
        Args:
            field_definitions: List of field definitions from type definition
            
        Returns:
            Dict mapping field names to SQL column names
        """
        field_mapping = {}
        
        for field_def in field_definitions:
            field_name = field_def.get("name")
            if field_name:
                # Create a simplified name for easier matching
                simple_name = field_name.split(":")[-1] if ":" in field_name else field_name
                field_mapping[simple_name] = f"[{field_name}]"
                
        return field_mapping
        
    def format_field_value(self, field_value: Any, field_type: str = "STRING_TYPE") -> Any:
        """
        Format a field value based on its type
        
        Args:
            field_value: Value to format
            field_type: OpenPages field type
            
        Returns:
            Formatted value
        """
        # Handle null values
        if field_value is None or field_value == "":
            return None
            
        # Handle enum types (need to be objects with name property)
        if field_type == "ENUM_TYPE":
            return {"name": field_value}
            
        # Handle other types
        if field_type == "INTEGER_TYPE":
            try:
                return int(field_value)
            except (ValueError, TypeError):
                return field_value
        elif field_type == "DECIMAL_TYPE":
            try:
                return float(field_value)
            except (ValueError, TypeError):
                return field_value
        elif field_type == "BOOLEAN_TYPE":
            if isinstance(field_value, str):
                return field_value.lower() in ("true", "yes", "1")
            return bool(field_value)
            
        # Default: return as is
        return field_value
        
    def extract_display_value(self, field_value: Any) -> str:
        """
        Extract a display value from a field value
        
        Args:
            field_value: Field value to extract from
            
        Returns:
            String representation of the value
        """
        # Handle null values
        if field_value is None:
            return "N/A"
            
        # Handle enum types (objects with name property)
        if isinstance(field_value, dict) and "name" in field_value:
            return field_value["name"]
            
        # Convert to string
        return str(field_value)
        
    def create_response_text(self, title: str, items: Dict[str, Any]) -> str:
        """
        Create a formatted response text
        
        Args:
            title: Title for the response
            items: Dictionary of items to include in the response
            
        Returns:
            Formatted response text
        """
        response_text = f"{title}\n\n"
        
        for key, value in items.items():
            display_value = self.extract_display_value(value)
            response_text += f"- **{key}**: {display_value}\n"
            
        return response_text

# Made with Bob
