"""
OpenPages MCP Server Implementation

This module implements a Machine Comprehension Protocol (MCP) server
that interfaces with IBM OpenPages to provide tools for managing issues,
controls, and other OpenPages objects.
"""

import os
import json
import logging
import pathlib
from typing import Dict, Any, List, Optional, Tuple, Union

from generic_object_tools import GenericObjectTools
from openpages_client import OpenPagesClient
from settings import settings, Settings

# Version information
__version__ = "1.0.0"

# Configure logging
logger = logging.getLogger(__name__)

class LocalMCPServer:
    """
    Local MCP Server implementation
    
    This class implements a Machine Comprehension Protocol (MCP) server that interfaces
    with IBM OpenPages. It provides tools for managing issues, controls, and other
    OpenPages objects through a JSON-RPC interface.
    """
    
    def __init__(self, custom_settings: Optional[Settings] = None) -> None:
        """
        Initialize the local MCP server
        
        Sets up the OpenPages client, initializes tool modules, and loads the tools schema.
        
        Args:
            custom_settings: Optional custom settings object to use instead of global settings
        """
        # Use provided settings or fall back to global settings
        self.settings = custom_settings if custom_settings else settings
        
        # Create OpenPages client
        # Double-check that the base URL has the correct protocol
        base_url = self.settings.OPENPAGES_BASE_URL
        if base_url and not (base_url.startswith('http://') or base_url.startswith('https://')):
            base_url = 'https://' + base_url
            logger.info(f"Added https:// protocol to base URL: {base_url}")
        
        # Log the final URL being used
        logger.info(f"Using OpenPages base URL: {base_url}")
        
        # Initialize the OpenPages client with authentication details
        try:
            self.client = OpenPagesClient(
                base_url,
                self.settings.OPENPAGES_AUTHENTICATION_TYPE,
                self.settings.OPENPAGES_USERNAME,
                self.settings.OPENPAGES_PASSWORD,
                self.settings.OPENPAGES_APIKEY,
                self.settings.OPENPAGES_AUTHENTICATION_URL,
                custom_settings=self.settings
            )
            logger.debug("OpenPages client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenPages client: {e}")
            raise RuntimeError(f"Failed to initialize OpenPages client: {e}")
        
        # Initialize tool modules
        try:
            # Initialize dynamic object tools based on configuration
            self.object_tools = {}
            for obj_config in self.settings.OPENPAGES_OBJECT_TYPES:
                obj_type = obj_config.get("type_id")
                tool_prefix = obj_config.get("tool_prefix")
                if obj_type and tool_prefix:
                    self.object_tools[tool_prefix] = GenericObjectTools(self.client, obj_config)
                    logger.debug(f"Initialized dynamic tool for {obj_type} with prefix {tool_prefix}")
            
            logger.debug("Tool modules initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize tool modules: {e}")
            raise RuntimeError(f"Failed to initialize tool modules: {e}")
        
        # Cache for type definitions to improve performance
        self.type_definitions: Dict[str, Any] = {}
        
        # Load tools schema from JSON file
        self._load_tools_schema()
        
        # Flag to indicate if dynamic schemas have been loaded
        self.dynamic_schemas_loaded: bool = False
        
    def _load_tools_schema(self) -> None:
        """
        Load tools schema from JSON file and dynamically add tools for configured object types
        
        First attempts to load the base tools schema from tools_schema.json in the same directory.
        Then dynamically adds tools for each object type configured in settings.
        Falls back to a minimal schema if the file can't be loaded.
        """
        try:
            # Get the path to the tools_schema.json file
            schema_path = pathlib.Path(__file__).parent / 'tools_schema.json'
            
            if not schema_path.exists():
                logger.warning(f"Tools schema file not found: {schema_path}")
                raise FileNotFoundError(f"Tools schema file not found: {schema_path}")
                
            # Load the schema from the file
            with open(schema_path, 'r', encoding='utf-8') as f:
                try:
                    self.tools = json.load(f)
                    logger.info(f"Loaded tools schema from {schema_path}")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in tools schema file: {e}")
                    raise
            
            # Dynamically add tools for each configured object type
            self._add_dynamic_tools_to_schema()
                    
        except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading tools schema: {e}")
            logger.warning("Using fallback minimal schema")
            # Fallback to a minimal schema if the file can't be loaded
            self.tools = [
                {
                    "name": "echo",
                    "description": "Echo the input text",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "The text to echo"
                            }
                        },
                        "required": ["text"]
                    }
                }
            ]
        except Exception as e:
            logger.error(f"Unexpected error loading tools schema: {e}")
            # Re-raise unexpected exceptions after logging
            raise RuntimeError(f"Failed to load tools schema: {e}") from e
        
    def _add_dynamic_tools_to_schema(self) -> None:
        """
        Dynamically add tools to the schema based on configured object types
        
        For each object type in settings.OPENPAGES_OBJECT_TYPES, adds the corresponding
        create, update, query, and delete tools to the schema.
        """
        logger.info("Adding dynamic tools to schema based on configured object types")
        
        # Keep track of existing tool names to avoid duplicates
        existing_tool_names = {tool["name"] for tool in self.tools}
        
        # Process each object type
        for obj_config in self.settings.OPENPAGES_OBJECT_TYPES:
            obj_type = obj_config.get("type_id")
            tool_prefix = obj_config.get("tool_prefix")
            display_name = obj_config.get("display_name", obj_type)
            
            # Ensure display_name is a string and not None
            if display_name is None:
                display_name = tool_prefix or "object"
            
            if not obj_type or not tool_prefix:
                logger.warning(f"Skipping invalid object type configuration: {obj_config}")
                continue
                
            logger.debug(f"Processing object type: {obj_type} with prefix {tool_prefix}")
            
            # Define the tools for this object type
            tools_to_add = []
            
            # Create tool
            create_tool_name = f"create_{tool_prefix}"
            if create_tool_name not in existing_tool_names:
                tools_to_add.append({
                    "name": create_tool_name,
                    "description": f"Create a new {display_name.lower()} in OpenPages",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": f"Name of the {display_name.lower()} (required)"
                            }
                        },
                        "required": ["name"]
                    }
                })
                
            # Update tool
            update_tool_name = f"update_{tool_prefix}"
            if update_tool_name not in existing_tool_names:
                tools_to_add.append({
                    "name": update_tool_name,
                    "description": f"Update an existing {display_name.lower()} in OpenPages",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_id": {
                                "type": "string",
                                "description": f"Resource ID of the {display_name.lower()} to update"
                            },
                            "path": {
                                "type": "string",
                                "description": f"Path of the {display_name.lower()} to update"
                            }
                        },
                        "required": ["name"]
                    }
                })
                
            # Query tool
            query_tool_name = f"query_{tool_prefix}s"
            if query_tool_name not in existing_tool_names:
                tools_to_add.append({
                    "name": query_tool_name,
                    "description": f"Query for {display_name.lower()}s in OpenPages",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": f"Filter {display_name.lower()}s by name (partial match, optional)"
                            },
                            "owner_filter": {
                                "type": "boolean",
                                "description": "Filter by current user ownership (default: False)"
                            },
                            "status_filter": {
                                "type": "string",
                                "description": f"Filter {display_name.lower()}s by status (optional)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": f"Maximum number of {display_name.lower()}s to return (default: 20)"
                            },
                            "sort_by": {
                                "type": "string",
                                "description": "Field to sort by (default: 'Name')"
                            },
                            "sort_order": {
                                "type": "string",
                                "description": "Sort order, 'ASC' or 'DESC' (default: 'ASC')"
                            },
                            "fields": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": []
                                },
                                "description": f"List of additional fields to include in the output (multiselect). Resource ID, Name, Description, and Status are always included."
                            }
                        }
                    }
                })
                
            # Delete tool
            delete_tool_name = f"delete_{tool_prefix}"
            if delete_tool_name not in existing_tool_names:
                tools_to_add.append({
                    "name": delete_tool_name,
                    "description": f"Delete an existing {display_name.lower()} in OpenPages",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_id": {
                                "type": "string",
                                "description": f"Resource ID of the {display_name.lower()} to delete. (Note: Either Resource_ID or Path is required.)"
                            },
                            "path": {
                                "type": "string",
                                "description": f"Path of the {display_name.lower()} including the name. (Note: Either Resource_ID or Path is required.)"
                            }
                        }
                    }
                })
                
            # Add the tools to the schema
            for tool in tools_to_add:
                self.tools.append(tool)
                existing_tool_names.add(tool["name"])
                logger.info(f"Added dynamic tool: {tool['name']}")
                
        # Calculate how many tools were added
        new_tool_count = len(self.tools) - len(existing_tool_names)
        logger.info(f"Added {new_tool_count} dynamic tools to schema")
    
    async def initialize_client(self) -> None:
        """
        Initialize the OpenPages client authentication
        
        Establishes authentication with the OpenPages server using the configured credentials.
        
        Raises:
            RuntimeError: If authentication fails
        """
        logger.info("Initializing OpenPages client authentication")
        try:
            await self.client.initialize_auth()
            logger.info("OpenPages client authentication initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenPages client authentication: {e}")
            raise RuntimeError(f"Authentication failed: {e}")
    
    async def load_dynamic_schemas(self) -> None:
        """
        Load dynamic schemas for tools
        
        Fetches schema information from OpenPages and updates tool schemas dynamically.
        This ensures that the tools have the most up-to-date field definitions.
        
        Returns:
            None
        """
        if self.dynamic_schemas_loaded:
            logger.debug("Dynamic schemas already loaded, skipping")
            return
        
        logger.info("Loading dynamic schemas for tools")
        
        try:
            # Initialize client authentication first
            await self.initialize_client()
            
            # Reload the tools schema to ensure we have the latest version with all object types
            self._load_tools_schema()
            
            # Load schemas for dynamic object types
            for obj_config in self.settings.OPENPAGES_OBJECT_TYPES:
                obj_type = obj_config.get("type_id")
                tool_prefix = obj_config.get("tool_prefix")
                display_name = obj_config.get("display_name", obj_type)
                
                if obj_type and tool_prefix:
                    # Create schema
                    logger.debug(f"Building dynamic schema for {obj_type}")
                    obj_schema = await self.build_dynamic_schema_for_object(obj_type, tool_prefix)
                    self._update_tool_schema(f"create_{tool_prefix}", obj_schema)
                    
                    # Update schema
                    update_obj_schema = self._create_update_schema(obj_schema, tool_prefix)
                    self._update_tool_schema(f"update_{tool_prefix}", update_obj_schema)
                    
                    # Query schema
                    query_obj_schema = await self.build_dynamic_schema_for_query_object(obj_type)
                    self._update_tool_schema(f"query_{tool_prefix}s", {
                        "type": "object",
                        "properties": query_obj_schema.get("properties", {}),
                        "description": f"Query for {display_name.lower() if display_name else tool_prefix}s in OpenPages"
                    })
                    
                    # Delete schema
                    delete_obj_schema = {
                        "type": "object",
                        "properties": {
                            "resource_id": {
                                "type": "string",
                                "description": f"Resource ID of the {tool_prefix} to delete"
                            },
                            "path": {
                                "type": "string",
                                "description": f"Path of the {tool_prefix} including the name"
                            }
                        },
                        "description": f"Delete a {display_name.lower() if display_name else tool_prefix} in OpenPages"
                    }
                    self._update_tool_schema(f"delete_{tool_prefix}", delete_obj_schema)
            
            self.dynamic_schemas_loaded = True
            logger.info("Successfully loaded all dynamic schemas")
            
        except Exception as e:
            logger.error(f"Error loading dynamic schemas: {e}")
            # Don't re-raise here to allow the server to continue with default schemas
    
    def _update_tool_schema(self, tool_name: str, schema: Dict[str, Any]) -> None:
        """
        Update a tool's schema
        
        Args:
            tool_name: Name of the tool to update
            schema: New schema to apply
        """
        for tool in self.tools:
            if tool["name"] == tool_name:
                tool["inputSchema"] = schema
                logger.info(f"Updated {tool_name} tool with dynamic schema")
                break
    
    def _create_update_schema(self, base_schema: Dict[str, Any], object_type: str) -> Dict[str, Any]:
        """
        Create an update schema based on a base schema
        
        Args:
            base_schema: Base schema to extend
            object_type: Type of object (e.g., "issue", "control")
            
        Returns:
            Dict containing the update schema
        """
        # Start with a copy of the base schema
        update_schema = {
            "type": "object",
            "properties": {},
            "required": ["name"]
        }
        
        # Add resource_id and path fields
        update_schema["properties"]["resource_id"] = {
            "type": "string",
            "description": f"Resource ID of the {object_type} to update. (Note: Either Resource_ID or Path is required.)"
        }
        update_schema["properties"]["path"] = {
            "type": "string",
            "description": f"Path of the {object_type} including the name. (Note: Either Resource_ID or Path is required.)"
        }
        
        # Copy all properties from base_schema
        for prop_name, prop_def in base_schema.get("properties", {}).items():
            update_schema["properties"][prop_name] = prop_def
        
        return update_schema
    
    async def get_type_definition(self, type_name: str) -> Optional[Dict[str, Any]]:
        """
        Get and cache type definition from OpenPages
        
        Retrieves the type definition for a given object type and caches it for future use.
        This improves performance for subsequent requests for the same type.
        
        Args:
            type_name: Name of the type to retrieve (e.g., "SOXIssue", "SOXControl")
            
        Returns:
            Dict containing the type definition or None if there was an error
        """
        if not type_name:
            logger.error("Invalid type_name: empty string")
            return None
            
        # Check cache first
        if type_name in self.type_definitions:
            logger.debug(f"Using cached type definition for {type_name}")
            return self.type_definitions[type_name]
        
        try:
            logger.info(f"Fetching type definition for {type_name}")
            type_def = await self.client.get_type_definition(type_name)
            
            if not type_def:
                logger.warning(f"Empty type definition returned for {type_name}")
                return None
                
            # Cache the result
            self.type_definitions[type_name] = type_def
            logger.debug(f"Cached type definition for {type_name}")
            return type_def
            
        except Exception as e:
            logger.error(f"Error fetching type definition for {type_name}: {e}")
            return None
    
    async def build_dynamic_schema_for_object(self, object_type: str, object_label: str = "") -> Dict[str, Any]:
        """
        Build a dynamic JSON schema for object creation based on field definitions
        
        Creates a JSON schema that describes the fields available for a given object type.
        This schema is used to validate and document the inputs for tools that create or
        update objects in OpenPages.
        
        Args:
            object_type: Type of object (e.g., "SOXIssue", "SOXControl")
            object_label: Label to use in descriptions (e.g., "issue", "control")
            
        Returns:
            Dict containing the JSON schema
        """
        # If object_label is not provided, derive it from object_type
        if not object_label:
            if "Issue" in object_type:
                object_label = "issue"
            elif "Model" in object_type:
                object_label = "model"
            elif "Control" in object_type:
                object_label = "control"
            elif "Risk" in object_type:
                object_label = "risk"
            else:
                object_label = "object"
        
        logger.debug(f"Building dynamic schema for {object_type} ({object_label})")
        
        # Start with basic schema
        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": f"Name of the {object_label} (required)"
                },
                "primaryParentId": {
                    "type": "string",
                    "description": "ID of the parent object, either as a numeric ID (e.g., 10101) or full path (e.g., /_op_sox/Project/Default/Issue/Parent-Issue.txt)"
                },
                "title": {
                    "type": "string",
                    "description": f"Title of the {object_label}"
                },
                "description": {
                    "type": "string",
                    "description": f"Description of the {object_label}"
                }
            },
            "required": ["name"]
        }
        
        # Try to get type definition
        type_def = await self.get_type_definition(object_type)
        if not type_def or "field_definitions" not in type_def:
            logger.warning(f"Could not get field definitions for {object_type}, using default schema")
            return schema
        
        # Common fields to skip (already included or system fields)
        skip_fields = [
            "Name", "Title", "Description", "Resource ID", 
            "Created By", "Creation Date", "Last Modification Date", 
            "Last Modified By", "Location"
        ]
        
        # Add fields from type definition
        for field in type_def.get("field_definitions", []):
            field_name = field.get("name")
            if not field_name or field_name in skip_fields:
                continue  # Skip fields already in schema or system fields
                
            # Convert OpenPages data type to JSON schema type
            field_type = field.get("data_type", "STRING_TYPE")
            json_type = "string"  # Default type
            json_format = None
            
            # Map OpenPages types to JSON schema types
            if field_type == "DATE_TYPE":
                json_type = "string"
                json_format = "date"
            elif field_type == "BOOLEAN_TYPE":
                json_type = "boolean"
            elif field_type == "INTEGER_TYPE":
                json_type = "integer"
            elif field_type == "DECIMAL_TYPE":
                json_type = "number"
            elif field_type == "ENUM_TYPE":
                json_type = "string"
                
            # Create property definition
            prop_def: Dict[str, Any] = {
                "type": json_type,
                "description": field.get("description") or f"Field: {field_name}"
            }
            
            # Add label information
            label = field.get("localized_label")
            if label:
                # Add label as metadata that can be used by the LLM
                prop_def["x-label"] = label
                
                # Include label in the description for better context
                prop_def["description"] = f"{label} ({field_name}): {prop_def['description']}"
            
            # Add format if applicable
            if json_format:
                prop_def["format"] = json_format
                
            # Add enum values if available
            enum_values = field.get("enum_values", [])
            if enum_values and field_type == "ENUM_TYPE":
                prop_def["enum"] = [v.get("name") for v in enum_values if v.get("name")]
                
            # Add to schema
            schema["properties"][field_name] = prop_def
            
            # Add to required list if field is required
            if field.get("required", False):
                schema["required"].append(field_name)
                
        logger.debug(f"Built schema for {object_type} with {len(schema['properties'])} properties")
        return schema
        
    async def build_dynamic_schema_for_query_object(self, object_type: str = "Model") -> Dict[str, Any]:
        """
        Build a dynamic JSON schema for query tools with field options
        
        Creates a schema that describes the available query parameters for a given object type.
        This includes fields that can be selected, filters, and sorting options.
        
        Args:
            object_type: Type of object (e.g., "Model", "SOXIssue", "SOXControl")
            
        Returns:
            Dict containing the JSON schema for query parameters
        """
        logger.debug(f"Building dynamic query schema for {object_type}")
        
        # Determine object label for descriptions
        object_label = "objects"
        if "Issue" in object_type:
            object_label = "issues"
        elif "Model" in object_type:
            object_label = "models"
        elif "Control" in object_type:
            object_label = "controls"
        elif "Risk" in object_type:
            object_label = "risks"
        
        # Start with basic schema
        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": f"Filter {object_label} by name (partial match, optional)"
                },
                "owner_filter": {
                    "type": "boolean",
                    "description": "Filter by current user ownership (default: False)"
                },
                "status_filter": {
                    "type": "string",
                    "description": f"Filter {object_label} by status (optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": f"Maximum number of {object_label} to return (default: 20)",
                    "minimum": 1,
                    "maximum": 100
                },
                "fetch_all_properties": {
                    "type": "boolean",
                    "description": f"Whether to fetch all main properties of the {object_label} (default: False)"
                },
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": []  # This will be populated with field names
                    },
                    "description": "List of additional fields to include in the output. Resource ID, Name, Description, and Status are always included."
                },
                "sort_by": {
                    "type": "string",
                    "description": "Field to sort by (default: 'Name')"
                },
                "sort_order": {
                    "type": "string",
                    "enum": ["ASC", "DESC"],
                    "description": "Sort order, 'ASC' or 'DESC' (default: 'ASC')"
                }
            }
        }
        
        # Try to get type definition
        type_def = await self.get_type_definition(object_type)
        if not type_def or "field_definitions" not in type_def:
            logger.warning(f"Could not get field definitions for {object_type}, using default schema")
            return schema
            
        # Map object types to their status field names
        status_field_mapping = {
            "SOXIssue": "OPSS-Iss:Status",
            "Model": "MRG-Model:Status",
            "SOXControl": "OPSS-Ctl:Status",
            "SOXRisk": "OPSS-Risk:Status"
        }
        
        # Determine status field name based on object type
        status_field_name = None
        for obj_type, field_name in status_field_mapping.items():
            if obj_type in object_type:
                status_field_name = field_name
                break
            
        # Find status field to get allowable values
        status_values = []
        # Keep track of enum fields to exclude from sort_by
        enum_fields = []
        
        # Process fields to extract status values and enum fields
        for field in type_def.get("field_definitions", []):
            field_name = field.get("name")
            field_type = field.get("data_type")
            
            if not field_name:
                continue
                
            # Handle Status field specifically
            if status_field_name and field_name == status_field_name:
                # Extract enum values if available
                enum_values = field.get("enum_values", [])
                if enum_values and field_type == "ENUM_TYPE":
                    status_values = [v.get("name") for v in enum_values if v.get("name")]
                    # Update status_filter with enum values
                    if status_values:
                        schema["properties"]["status_filter"] = {
                            "type": "string",
                            "enum": status_values,
                            "description": f"Filter {object_label} by status (optional)"
                        }
                        logger.debug(f"Added {len(status_values)} status values to schema")
            
            # Track all enum fields to exclude from sort_by
            if field_type == "ENUM_TYPE":
                # Create a simplified name for display
                if ':' in field_name:
                    field_group, simple_name = field_name.split(':', 1)
                    display_name = f"{simple_name} [{field_group}]"
                else:
                    display_name = field_name
                enum_fields.append(display_name)
        
        # Determine which fields to skip based on object type
        skip_fields = ["Resource ID", "Name", "Description"]
        if status_field_name:
            skip_fields.append(status_field_name)
                
        # Extract field names for enum values
        field_names = []
        for field in type_def.get("field_definitions", []):
            field_name = field.get("name")
            
            if not field_name or field_name in skip_fields:
                continue  # Skip fields already included by default
                
            # Extract field group and name
            if ':' in field_name:
                field_group, simple_name = field_name.split(':', 1)
                # Format as "Name [Group]"
                display_name = f"{simple_name} [{field_group}]"
            else:
                display_name = field_name
                
            field_names.append(display_name)
        
        # Add common field names that might not be in the type definition
        common_fields_mapping = {
            "SOXIssue": ["Priority [OPSS-Iss]", "Owner", "Due Date [OPSS-Iss]"],
            "Model": ["Owner", "Last Modified Date", "Creation Date"],
            "SOXControl": ["Owner", "Control Frequency", "Automation Status"],
            "SOXRisk": ["Owner", "Risk Level", "Impact"]
        }
        
        # Add common fields for this object type
        for obj_type, fields in common_fields_mapping.items():
            if obj_type in object_type:
                for field in fields:
                    if field not in field_names:
                        field_names.append(field)
        
        # Sort field names for better readability
        field_names.sort()
        
        # Add enum values to the fields property
        if field_names:
            schema["properties"]["fields"]["items"]["enum"] = field_names
            logger.info(f"Added {len(field_names)} field options to the schema for {object_type}")
            
            # Create a list of sortable fields (excluding enum types)
            sortable_fields = ["Name", "Resource ID", "Description"]
            for field in field_names:
                if field not in enum_fields:
                    sortable_fields.append(field)
            
            # Remove sort_order as a separate property since it will be part of each sort field
            if "sort_order" in schema["properties"]:
                del schema["properties"]["sort_order"]
            
            # Replace sort_by with an array of objects that include field and order
            schema["properties"]["sort_by"] = {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {
                            "type": "string",
                            "enum": sortable_fields,
                            "description": "Field to sort by"
                        },
                        "order": {
                            "type": "string",
                            "enum": ["ASC", "DESC"],
                            "description": "Sort order (ascending or descending)"
                        }
                    },
                    "required": ["field", "order"]
                },
                "description": "Fields to sort by with individual sort orders (up to 3 fields)",
                "maxItems": 3
            }
        
        logger.debug(f"Built query schema for {object_type} with {len(field_names)} available fields")
        return schema
    
    async def update_query_issues_schema(self) -> Dict[str, Any]:
        """
        Update the query_issues tool schema with dynamic field options
        
        Builds a schema for the query_issues tool that includes all available fields
        and filtering options for SOXIssue objects.
        
        Returns:
            Dict containing the updated tool definition
        """
        logger.debug("Updating query_issues schema")
        
        try:
            # Get dynamic schema for query_issues
            issue_schema = await self.build_dynamic_schema_for_query_object("SOXIssue")
            
            # Return the updated tool definition
            return {
                "name": "query_issues",
                "description": "Query for issues in OpenPages with filtering and field selection",
                "inputSchema": issue_schema
            }
        except Exception as e:
            logger.error(f"Error updating query_issues schema: {e}")
            # Return default schema if there's an error
            return {
                "name": "query_issues",
                "description": "Query for issues in OpenPages",
                "inputSchema": self._get_default_query_schema("issues")
            }
            
    async def update_query_controls_schema(self) -> Dict[str, Any]:
        """
        Update the query_controls tool schema with dynamic field options
        
        Builds a schema for the query_controls tool that includes all available fields
        and filtering options for SOXControl objects.
        
        Returns:
            Dict containing the updated tool definition
        """
        logger.debug("Updating query_controls schema")
        
        try:
            # Get dynamic schema for query_controls
            control_schema = await self.build_dynamic_schema_for_query_object("SOXControl")
            
            # Return the updated tool definition
            return {
                "name": "query_controls",
                "description": "Query for controls in OpenPages with filtering and field selection",
                "inputSchema": control_schema
            }
        except Exception as e:
            logger.error(f"Error updating query_controls schema: {e}")
            # Return default schema if there's an error
            return {
                "name": "query_controls",
                "description": "Query for controls in OpenPages",
                "inputSchema": self._get_default_query_schema("controls")
            }
    
    def _get_default_query_schema(self, object_label: str) -> Dict[str, Any]:
        """
        Get a default query schema for when dynamic schema generation fails
        
        Args:
            object_label: Label for the object type (e.g., "issues", "controls")
            
        Returns:
            Dict containing a basic query schema
        """
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": f"Filter {object_label} by name (partial match, optional)"
                },
                "owner_filter": {
                    "type": "boolean",
                    "description": "Filter by current user ownership (default: False)"
                },
                "status_filter": {
                    "type": "string",
                    "description": f"Filter {object_label} by status (optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": f"Maximum number of {object_label} to return (default: 20)",
                    "minimum": 1,
                    "maximum": 100
                },
                "fetch_all_properties": {
                    "type": "boolean",
                    "description": f"Whether to fetch all main properties of the {object_label} (default: False)"
                },
                "sort_by": {
                    "type": "string",
                    "description": "Field to sort by (default: 'Name')"
                },
                "sort_order": {
                    "type": "string",
                    "enum": ["ASC", "DESC"],
                    "description": "Sort order, 'ASC' or 'DESC' (default: 'ASC')"
                },
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": []  # Empty since we couldn't get field names
                    },
                    "description": f"List of additional fields to include in the output. Resource ID, Name, Description, and Status are always included."
                }
            }
        }
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle initialize request from the client
        
        Initializes the server and returns server information and capabilities.
        
        Args:
            params: Parameters from the initialize request
            
        Returns:
            Dict containing server information and capabilities
        """
        logger.info("Handling initialize request")
        
        # Reload the tools schema to ensure we have all object types
        self._load_tools_schema()
        
        # We don't load dynamic schemas here to make initialization faster
        # They will be loaded when list_tools is called
        
        return {
            "protocolVersion": "2025-03-26",
            "serverInfo": {
                "name": "local-mcp-server",
                "version": __version__,
                "description": "A local MCP server for IBM OpenPages integration"
            },
            "capabilities": {
                "tools": {
                    "list": {
                        "enabled": True
                    },
                    "call": {
                        "enabled": True
                    },
                    "invoke": {
                        "enabled": True
                    }
                },
                "resources": {
                    "list": {
                        "enabled": False
                    },
                    "read": {
                        "enabled": False
                    }
                },
                "prompts": {
                    "list": {
                        "enabled": False
                    }
                },
                "completion": {
                    "enabled": True
                }
            },
            "tools": self.tools
        }
    
    async def handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle list_tools request from the client
        
        Returns the list of available tools with their schemas.
        
        Args:
            params: Parameters from the list_tools request
            
        Returns:
            Dict containing the list of tools
        """
        logger.info("Handling list_tools request")
        
        try:
            # Reload the tools schema to ensure we have the latest version
            # This will include any new object types from object_types.json
            self._load_tools_schema()
            
            # Load dynamic schemas to ensure tools have up-to-date field definitions
            await self.load_dynamic_schemas()
            
            # Log the number of tools being returned
            logger.info(f"Returning {len(self.tools)} tools in schema")
            
            return {
                "tools": self.tools
            }
        except Exception as e:
            logger.error(f"Error handling list_tools request: {e}")
            # Return the tools without dynamic schemas
            return {
                "tools": self.tools
            }
    
    async def _handle_echo_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the echo tool"""
        text = arguments.get("text", "")
        return {
            "result": [
                {"type": "text", "text": f"Echo: {text}"}
            ]
        }
    
    async def _handle_generic_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle any generic tool based on the tool name
        
        Args:
            tool_name: Name of the tool to handle
            arguments: Tool arguments
            
        Returns:
            Dict containing the tool execution result
        """
        # Parse the tool name to determine the operation and object type
        parts = tool_name.split('_', 1)
        if len(parts) != 2:
            return {
                "result": [
                    {"type": "text", "text": f"Invalid tool name format: {tool_name}"}
                ]
            }
            
        operation = parts[0]  # create, update, query, delete
        obj_type = parts[1]   # control, issue, etc.
        
        # Handle plural form for query operations
        if obj_type.endswith('s') and operation == 'query':
            obj_type = obj_type[:-1]
            
        # Check if we have a tool for this object type
        if obj_type not in self.object_tools:
            return {
                "result": [
                    {"type": "text", "text": f"No tool available for object type: {obj_type}"}
                ]
            }
            
        # Get the appropriate tool
        tool = self.object_tools[obj_type]
        
        try:
            # Call the appropriate method based on the operation
            if operation == 'create':
                result = await tool.create_object(arguments)
            elif operation == 'update':
                result = await tool.update_object(arguments)
            elif operation == 'query':
                result = await tool.query_objects(arguments)
            elif operation == 'delete':
                result = await tool.delete_object(arguments)
            else:
                return {
                    "result": [
                        {"type": "text", "text": f"Unknown operation: {operation}"}
                    ]
                }
                
            # Format the response
            return {
                "result": [{"type": "text", "text": item.text} for item in result]
            }
            
        except Exception as e:
            logger.error(f"Error handling {tool_name}: {e}", exc_info=True)
            return {
                "result": [
                    {"type": "text", "text": f"Error handling {tool_name}: {str(e)}"}
                ]
            }
    
    async def handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle call_tool request from the client
        
        Executes the requested tool with the provided arguments.
        
        Args:
            params: Parameters from the call_tool request, including tool name and arguments
            
        Returns:
            Dict containing the tool execution result
        """
        name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        if not name:
            logger.error("Tool name not provided in call_tool request")
            return {
                "result": [
                    {"type": "text", "text": "Error: Tool name not provided"}
                ]
            }
        
        logger.info(f"Handling call_tool request for tool: {name}")
        logger.debug(f"Tool arguments: {arguments}")
        
        try:
            # Map special tool names to their handler methods
            special_tool_handlers = {
                "echo": self._handle_echo_tool
            }
            
            # Check if this is a special tool
            if name in special_tool_handlers:
                return await special_tool_handlers[name](arguments)
            
            # Handle all other tools using the generic handler
            return await self._handle_generic_tool(name, arguments)
                
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}", exc_info=True)
            return {
                "result": [
                    {"type": "text", "text": f"Error calling tool {name}: {str(e)}"}
                ]
            }
    
    async def handle_shutdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle shutdown request from the client
        
        Performs any necessary cleanup before shutting down.
        
        Args:
            params: Parameters from the shutdown request
            
        Returns:
            Empty dict
        """
        logger.info("Handling shutdown request")
        # Perform any cleanup here if needed
        return {}
    
    async def process_request(self, request_data: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Process a JSON-RPC request
        
        Handles different JSON-RPC methods and routes them to the appropriate handlers.
        
        Args:
            request_data: The JSON-RPC request data
            
        Returns:
            Tuple containing (response_data, should_exit)
        """
        method = request_data.get("method", "")
        params = request_data.get("params", {})
        request_id = request_data.get("id")
        
        if not method:
            logger.error("Missing method in JSON-RPC request")
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: missing method"
                },
                "id": request_id
            }, False
        
        logger.info(f"Processing request: {method} (ID: {request_id})")
        
        try:
            # Handle different methods
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method in ["x", "tools/list"]:
                result = await self.handle_list_tools(params)
            elif method in ["call_tool", "tools/call", "tools/invoke"]:
                logger.debug("Calling tool API")
                response = await self.handle_call_tool(params)
                
                # Format the response in the exact format requested
                formatted_response = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(response)
                        }
                    ],
                    "isError": False
                }
                result = formatted_response
                logger.debug("Tool API call completed")
            elif method == "shutdown":
                result = await self.handle_shutdown(params)
                response = {
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": request_id
                }
                return response, True
            else:
                # Method not supported
                logger.warning(f"Unsupported method: {method}")
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    },
                    "id": request_id
                }, False
            
            # Send the response
            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }, False
            
        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": request_id
            }, False

# Made with Bob
