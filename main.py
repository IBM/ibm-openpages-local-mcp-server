from mcp.server.fastmcp import FastMCP  # Import FastMCP to create MCP server
import math  # Import Python's math module for factorial calculation
import sys
from issue_tools import IssueTools
from control_tools import ControlTools
from mcp.types import TextContent
from typing import Dict, Any, List
from openpages_client import OpenPagesClient

import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional

# Import OpenPages client and tools
from settings import settings

# Configure logging to stderr only (no stdout pollution)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

 # Create the MCP server instance and give it a name
# mcp = FastMCP("math-tools-mcp")


# # client = OpenPagesClient(
# #             'https://openpages-ai1.fyre.ibm.com:10111',
# #             'OpenPagesAdministrator',
# #             'passw0rd'
# #         )
# client = OpenPagesClient(
#             'https://c5f3e0f9-5891-4291-b0cb-b31176d90edd.us-east-1.aws.qa.openpages.ibm.com',
#             '_RkEG4u6YHAnokeJoYF4UQpc9SvR6jWRkvfhIiLQNR1z'
#         )
# issue_tools = IssueTools(client)

#  # Uplift Python's big-int to string safety cap
# if hasattr(sys, "set_int_max_str_digits"):
#     sys.set_int_max_str_digits(1000000)


# # -----------------------------------
#  # Helper function (not a tool)
#  # ------------------------------------

# def compute_factorial(n: int) -> int:
#      """
#      Return n! as an integer.
#      This is a shared helper for both MCP tools below.
#      """
#      # Check that n is a non-negative integer
#      if not isinstance(n, int) or n < 0:
#          raise ValueError("n must be a non-negative integer")

#      # Use Python's built-in factorial function
#      return math.factorial(n)

# # ----------------------------
#  # MCP Tool 1: factorial_value
#  # ----------------------------

# @mcp.tool("factorial_value")
# async def factorial_value(n: int) -> int:
#      """
#      Return the exact value of n! (factorial of n).
#      Example:
#          factorial_value(5) -> 120
#      """

#      # Use the helper function to compute the factorial
#      return compute_factorial(n)


# # # ----------------------------
# #  # MCP Tool 2: factorial_digits
# #  # ----------------------------
# # @mcp.tool("factorial_digits")
# # async def factorial_digits(n: int) -> int:
# #      """
# #      Return the number of digits in n! (factorial of n).
# #      Example:
# #          factorial_digits(5) -> 3
# #      """
# #      # Get the factorial using the same helper function
# #      fact_value = compute_factorial(n)

# #      # Convert to string and count how many characters (digits) it has
# #      return len(str(fact_value))

# # ----------------------------
#  # MCP Tool 1: openpages_create_issue
#  # ----------------------------
# @mcp.tool("openpages_create_issue")
# async def openpages_create_issue(issue_request: Dict[str, Any]) ->  Dict[str, Any]:
#      """
#      Create an Issue
#      Example:
#          openpages_create_issue ({"name":"Accounts Receivable - 2011 - ISS001", "description":"Certification requirements lacking"})-> {"type": "text","text": "Successfully created Issue:\\n\\n- **Name**: Accounts Receivable - 2011 - ISS001\\n- **Resource ID**: 15070\\n- **Type**: SOXIssue\\n- **Description**: "Certification requirements lacking"    }]
#      """

#      result: List[TextContent] = await issue_tools.create_issue(issue_request)
#      return {
#                     "result": [{"type": "text", "text": item.text} for item in result]
#                 }


# --------------------------------
 # Start MCP server if run directly
 # --------------------------------
# if __name__ == "__main__":
#      # Start the MCP server so the MCP tools can be called by watsonx Orchestrate or any LLM.
#      mcp.run()

def load_dotenv(dotenv_path='.env'):
    """Load environment variables from .env file"""
    try:
        if os.path.exists(dotenv_path):
            with open(dotenv_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    key, value = line.split('=', 1)
                    os.environ[key] = value
            return True
        return False
    except Exception as e:
        logger.error(f"Error loading .env file: {e}")
        return False
    
class LocalMCPServer:
    """Local MCP Server implementation"""
    
    def __init__(self):
        """Initialize the local MCP server"""
        # Create OpenPages client
        # Double-check that the base URL has the correct protocol
        base_url = settings.OPENPAGES_BASE_URL
        if base_url and not (base_url.startswith('http://') or base_url.startswith('https://')):
            base_url = 'https://' + base_url
            logger.info(f"Added https:// protocol to base URL: {base_url}")
        
        # Log the final URL being used
        logger.info(f"Using OpenPages base URL: {base_url}")
        
        self.client = OpenPagesClient(
            base_url,
            settings.OPENPAGES_AUTHENTICATION_TYPE,
            settings.OPENPAGES_USERNAME,
            settings.OPENPAGES_PASSWORD,
            settings.OPENPAGES_APIKEY,
            settings.OPENPAGES_AUTHENTICATION_URL
        )
        
        # Initialize tool modules
        #self.risk_tools = RiskTools(self.client)
        self.issue_tools = IssueTools(self.client)
        self.control_tools = ControlTools(self.client)
        #self.query_tools = QueryTools(self.client)
        
        # Cache for type definitions
        self.type_definitions = {}
        
        # Define available tools with basic schemas
        self._init_tools()
        
        # Flag to indicate if dynamic schemas have been loaded
        self.dynamic_schemas_loaded = False
        
    def _init_tools(self):
        """Initialize tools with basic schemas"""
        # Define available tools
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
            },
            # Other tools...
        ]
        # Tools are defined in the class initialization
        
    async def initialize_client(self):
        """Initialize the OpenPages client authentication"""
        logger.info("Initializing OpenPages client authentication")
        await self.client.initialize_auth()
        logger.info("OpenPages client authentication initialized")
    
    async def load_dynamic_schemas(self):
        """Load dynamic schemas for tools"""
        if self.dynamic_schemas_loaded:
            return
        
        # Initialize client authentication first
        await self.initialize_client()

        # Define available tools
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
            },
            {
                "name": "create_control",
                "description": "Create a new control in OpenPages",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the control (required)"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "update_control",
                "description": "Update an existing control in OpenPages",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resource_id": {
                            "type": "string",
                            "description": "Resource ID of the control to update (required)"
                        }
                    },
                    "required": ["resource_id"]
                }
            },
            #create_issue tool will be populated with dynamic schema during initialization
            {
                "name": "create_issue",
                "description": "Create a new issue in OpenPages",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the issue (required)"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "update_issue",
                "description": "Update an existing issue in OpenPages",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resource_id": {
                            "type": "string",
                            "description": "Resource ID of the issue to update (required)"
                        }
                    },
                    "required": ["resource_id"]
                }
            },
            {
                "name": "query_issues",
                "description": "Query for issues in OpenPages",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Filter issues by name (partial match, optional)"
                        },
                        "owner_filter": {
                            "type": "boolean",
                            "description": "Filter by current user ownership (default: False)"
                        },
                        "status_filter": {
                            "type": "string",
                            "description": "Filter issues by status (optional)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of issues to return (default: 20)"
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
                                "enum": []  # This will be populated with field names
                            },
                            "description": "List of additional fields to include in the output (multiselect). Resource ID, Name, Description, and Status are always included. Available fields: Priority, Owner, Due Date, and others from the issue type definition."
                        }
                    }
                }
            },
            {
                "name": "custom_query",
                "description": "Execute a custom OpenPages query",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL-like query statement for OpenPages"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
            
        try:
            # Get dynamic schema for create_issue
            issue_schema = await self.build_dynamic_schema_for_object("SOXIssue", "issue")
            # Update the create_issue tool schema
            for tool in self.tools:
                if tool["name"] == "create_issue":
                    tool["inputSchema"] = issue_schema
                    logger.info("Updated create_issue tool with dynamic schema")
                    break
            
            # Update the update_issue tool schema
            for tool in self.tools:
                if tool["name"] == "update_issue":
                    # Start with a copy of the issue schema
                    update_schema = {
                        "type": "object",
                        "properties": {},
                        "required": ["resource_id", "name"]
                    }
                    
                    # Add resource_id field
                    update_schema["properties"]["resource_id"] = {
                        "type": "string",
                        "description": "Resource ID of the issue to update (required)"
                    }
                    
                    # Copy all properties from issue_schema including 'name'
                    for prop_name, prop_def in issue_schema.get("properties", {}).items():
                        update_schema["properties"][prop_name] = prop_def
                    
                    # Set the updated schema
                    tool["inputSchema"] = update_schema
                    logger.info("Updated update_issue tool with dynamic schema (including name as required)")
                    break

            # Get dynamic schema for query_issues
            query_issues_tool = await self.update_query_issues_schema()
            
            # Update the query_issues tool schema
            for tool in self.tools:
                if tool["name"] == "query_issues":
                    tool["inputSchema"] = query_issues_tool["inputSchema"]
                    logger.info("Updated query_issues tool with dynamic schema")
                    break
                    
            # Get dynamic schema for create_control
            control_schema = await self.build_dynamic_schema_for_object("SOXControl", "control")
            # Update the create_control tool schema
            for tool in self.tools:
                if tool["name"] == "create_control":
                    tool["inputSchema"] = control_schema
                    logger.info("Updated create_control tool with dynamic schema")
                    break
            
            # Update the update_control tool schema
            for tool in self.tools:
                if tool["name"] == "update_control":
                    # Start with a copy of the control schema
                    update_schema = {
                        "type": "object",
                        "properties": {},
                        "required": ["resource_id", "name"]
                    }
                    
                    # Add resource_id field
                    update_schema["properties"]["resource_id"] = {
                        "type": "string",
                        "description": "Resource ID of the control to update (required)"
                    }
                    
                    # Copy all properties from control_schema including 'name'
                    for prop_name, prop_def in control_schema.get("properties", {}).items():
                        update_schema["properties"][prop_name] = prop_def
                    
                    # Set the updated schema
                    tool["inputSchema"] = update_schema
                    logger.info("Updated update_control tool with dynamic schema (including name as required)")
                    break

            # Get dynamic schema for query_controls
            query_controls_tool = await self.update_query_controls_schema()
            
            # Update the query_controls tool schema
            for tool in self.tools:
                if tool["name"] == "query_controls":
                    tool["inputSchema"] = query_controls_tool["inputSchema"]
                    logger.info("Updated query_controls tool with dynamic schema")
                    break
            self.dynamic_schemas_loaded = True
        except Exception as e:
            logger.error(f"Error loading dynamic schemas: {e}")
        
        
    
    async def get_type_definition(self, type_name: str) -> Optional[Dict[str, Any]]:
        """
        Get and cache type definition
        
        Args:
            type_name: Name of the type to retrieve
            
        Returns:
            Type definition data or None if there was an error
        """
        if type_name in self.type_definitions:
            logger.info(f"Using cached type definition for {type_name}")
            return self.type_definitions[type_name]
        
        try:
            logger.info(f"Fetching type definition for {type_name}")
            type_def = await self.client.get_type_definition(type_name)
            self.type_definitions[type_name] = type_def
            return type_def
        except Exception as e:
            logger.error(f"Error fetching type definition for {type_name}: {e}")
            return None
    
    async def build_dynamic_schema_for_object(self, object_type: str, object_label: str = ""):
        """
        Build a dynamic JSON schema for object creation based on field definitions
        
        Args:
            object_type: Type of object (e.g., SOXIssue, Model)
            object_label: Label to use in descriptions (e.g., "issue", "model")
            
        Returns:
            JSON schema object
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
        
        # Start with basic schema
        schema = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": f"Name of the {object_label} (required)"
                },
                "primaryParentId": {
                    "type": "string",
                    "description": "Id of another Object Type's ID, such as 10101, or its full path, such as /_op_sox/Project/Default/Issue/Parent-Issue.txt"
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
        
        # Add fields from type definition
        for field in type_def.get("field_definitions", []):
            field_name = field.get("name")
            if not field_name or field_name in ["Name", "Title", "Description", "Resource ID", "Created By", "Creation Date", "Last Modification Date", "Last Modified By", "Location"]:
                continue  # Skip fields already in schema
                
            # Convert OpenPages data type to JSON schema type
            field_type = field.get("data_type", "STRING_TYPE")
            json_type = "string"
            json_format = None
            
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
            prop_def = {
                "type": json_type,
                "description": field.get("description", f"Field: {field_name}")
            }
            
            # Add format if applicable
            if json_format:
                prop_def["format"] = json_format
                
            # Add enum values if available
            enum_values = field.get("enum_values", [])
            if enum_values and field_type == "ENUM_TYPE":
                prop_def["enum"] = [v.get("name") for v in enum_values]
                
            # Add to schema
            schema["properties"][field_name] = prop_def
            
            # Add to required list if field is required
            if field.get("required", False):
                if "required" not in schema:
                    schema["required"] = ["name"]
                schema["required"].append(field_name)
                
        return schema
        
    async def build_dynamic_schema_for_query_object(self, object_type: str = "Model"):
        """
        Build a dynamic JSON schema for query tools with field options
        
        Args:
            object_type: Type of object (e.g., Model, SOXIssue)
            
        Returns:
            JSON schema object for the fields property
        """
        # Start with basic schema
        schema = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Filter models by name (partial match, optional)"
                },
                "owner_filter": {
                    "type": "boolean",
                    "description": "Filter by current user ownership (default: False)"
                },
                "status_filter": {
                    "type": "string",
                    "description": "Filter models by status (optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of models to return (default: 20)"
                },
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": []  # This will be populated with field names
                    },
                    "description": "List of additional fields to include in the output (multiselect). Resource ID, Name, Description, and Status are always included."
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
            
        # Determine status field name based on object type
        status_field_name = None
        if "Issue" in object_type:
            status_field_name = "OPSS-Iss:Status"
        elif "Model" in object_type:
            status_field_name = "MRG-Model:Status"
        elif "Control" in object_type:
            status_field_name = "OPSS-Ctrl:Status"
        elif "Risk" in object_type:
            status_field_name = "OPSS-Risk:Status"
            
        # Find status field to get allowable values
        status_values = []
        # Keep track of enum fields to exclude from sort_by
        enum_fields = []
        
        for field in type_def.get("field_definitions", []):
            field_name = field.get("name")
            field_type = field.get("data_type")
            
            # Handle Status field specifically
            if status_field_name and field_name == status_field_name:
                # Extract enum values if available
                enum_values = field.get("enum_values", [])
                if enum_values and field_type == "ENUM_TYPE":
                    status_values = [v.get("name") for v in enum_values]
                    # Update status_filter with enum values
                    schema["properties"]["status_filter"] = {
                        "type": "string",
                        "enum": status_values,
                        "description": "Filter by status (optional)"
                    }
            
            # Track all enum fields to exclude from sort_by
            if field_type == "ENUM_TYPE":
                # Create a simplified name for display
                if ':' in field_name:
                    field_group, simple_name = field_name.split(':', 1)
                    display_name = f"{simple_name} [{field_group}]"
                else:
                    display_name = field_name
                enum_fields.append(display_name)
        
        # Extract field names for enum values
        field_names = []
        for field in type_def.get("field_definitions", []):
            field_name = field.get("name")
            # Determine which fields to skip based on object type
            skip_fields = ["Resource ID", "Name", "Description"]
            if "Issue" in object_type:
                skip_fields.append("OPSS-Iss:Status")
            elif "Model" in object_type:
                skip_fields.append("MRG-Model:Status")
            elif "Control" in object_type:
                skip_fields.append("OPSS-Ctrl:Status")
            elif "Risk" in object_type:
                skip_fields.append("OPSS-Risk:Status")
                
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
        common_fields = []
        if "Issue" in object_type:
            common_fields = ["Priority [OPSS-Iss]", "Owner", "Due Date [OPSS-Iss]"]
        elif "Model" in object_type:
            common_fields = ["Owner", "Last Modified Date", "Creation Date"]
        elif "Control" in object_type:
            common_fields = ["Owner", "Control Frequency", "Automation Status"]
        elif "Risk" in object_type:
            common_fields = ["Owner", "Risk Level", "Impact"]
        for field in common_fields:
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
            
            # Add enum values to the fields property
            if field_names:
                schema["properties"]["fields"]["items"]["enum"] = field_names
        
        return schema
    
    async def update_query_issues_schema(self):
        """
        Update the query_issues tool schema with dynamic field options
        
        Returns:
            Updated tool definition
        """
        try:
            # Get dynamic schema for query_issues
            issue_schema = await self.build_dynamic_schema_for_query_object("SOXIssue")
            
            # Return the updated tool definition
            return {
                "name": "query_issues",
                "description": "Query for issues in OpenPages",
                "inputSchema": issue_schema
            }
        except Exception as e:
            logger.error(f"Error updating query_issues schema: {e}")
            # Return default schema if there's an error
            return {
                "name": "query_issues",
                "description": "Query for issues in OpenPages",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Filter issues by name (partial match, optional)"
                        },
                        "owner_filter": {
                            "type": "boolean",
                            "description": "Filter by current user ownership (default: False)"
                        },
                        "status_filter": {
                            "type": "string",
                            "description": "Filter issues by status (optional)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of issues to return (default: 20)"
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
                                "enum": []  # This will be populated with field names
                            },
                            "description": "List of additional fields to include in the output (multiselect). Resource ID, Name, Description, and Status are always included."
                        }
                    }
                }
            }
            
    async def update_query_controls_schema(self):
        """
        Update the query_controls tool schema with dynamic field options
        
        Returns:
            Updated tool definition
        """
        try:
            # Get dynamic schema for query_issues
            control_schema = await self.build_dynamic_schema_for_query_object("SOXControl")
            
            # Return the updated tool definition
            return {
                "name": "query_controls",
                "description": "Query for controls in OpenPages",
                "inputSchema": control_schema
            }
        except Exception as e:
            logger.error(f"Error updating query_controls schema: {e}")
            # Return default schema if there's an error
            return {
                "name": "query_controls",
                "description": "Query for controls in OpenPages",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Filter issues by name (partial match, optional)"
                        },
                        "owner_filter": {
                            "type": "boolean",
                            "description": "Filter by current user ownership (default: False)"
                        },
                        "status_filter": {
                            "type": "string",
                            "description": "Filter controls by status (optional)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of issues to return (default: 20)"
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
                                "enum": []  # This will be populated with field names
                            },
                            "description": "List of additional fields to include in the output (multiselect). Resource ID, Name, Description, and Status are always included."
                        }
                    }
                }
            }
    
    async def handle_initialize(self, params):
        """Handle initialize request"""
        logger.info("Handling initialize request")
        
        # Load dynamic schemas
        #await self.load_dynamic_schemas()
        return {
            "protocolVersion": "2025-03-26",
            "serverInfo": {
                "name": "local-mcp-server",
                "version": "1.0.0",
                "description": "A local MCP server using actual OpenPages APIs"
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
    
    async def handle_list_tools(self, params):
        """Handle list_tools request"""
        logger.info("Handling list_tools request")
        
        # Load dynamic schemas
        await self.load_dynamic_schemas()

        return {
            "tools": self.tools
        }
    
    async def handle_call_tool(self, params):
        """Handle call_tool request"""
        name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        logger.info(f"Handling call_tool request for tool: {name}")
        
        try:
            if name == "echo":
                text = arguments.get("text", "")
                return {
                    "result": [
                        {"type": "text", "text": f"Echo: {text}"}
                    ]
                }
            elif name == "create_issue":
                # Use the actual issue_tools implementation
                result = await self.issue_tools.create_issue(arguments)
                # Format the response exactly as requested
                response_text = ""
                for item in result:
                    response_text = item.text
                return {
                    "result": [{"type": "text", "text": response_text}]
                }
            elif name == "query_issues":
                # Use the actual issue_tools implementation
                result = await self.issue_tools.query_issues(arguments)
                return {
                    "result": [{"type": "text", "text": item.text} for item in result]
                }
            elif name == "update_issue":
                # Use the actual issue_tools implementation
                result = await self.issue_tools.update_issue(arguments)
                return {
                    "result": [{"type": "text", "text": item.text} for item in result]
                }
            elif name == "create_control":
                # Use the actual control_tools implementation
                result = await self.control_tools.create_control(arguments)
                # Format the response exactly as requested
                response_text = ""
                for item in result:
                    response_text = item.text
                return {
                    "result": [{"type": "text", "text": response_text}]
                }
            elif name == "update_control":
                # Use the actual control_tools implementation
                result = await self.control_tools.update_control(arguments)
                return {
                    "result": [{"type": "text", "text": item.text} for item in result]
                }
            else:
                return {
                    "result": [
                        {"type": "text", "text": f"Tool not found: {name}"}
                    ]
                }
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            return {
                "result": [
                    {"type": "text", "text": f"Error calling tool {name}: {str(e)}"}
                ]
            }
    
    async def handle_shutdown(self, params):
        """Handle shutdown request"""
        logger.info("Handling shutdown request")
        return {}
    
    async def process_request(self, request_data):
        """Process a JSON-RPC request"""
        method = request_data.get("method", "")
        params = request_data.get("params", {})
        request_id = request_data.get("id")
        
        logger.info(f"Processing request: {method} (ID: {request_id})")
        
        # Handle different methods
        if method == "initialize":
            result = await self.handle_initialize(params)
        elif method == "list_tools" or method == "tools/list":
            result = await self.handle_list_tools(params)
        elif method == "call_tool" or method == "tools/call" or method == "tools/invoke":
            logger.info(f"calling api .....")
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
            logger.info(f"received response {result}")
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

async def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()
    
    logger.info("Local MCP server starting...")
    
    # Create server instance
    server = LocalMCPServer()
    
    # Initialize client authentication
    await server.initialize_client()
    logger.info("Client authentication initialized")
    
    # Process JSON-RPC messages from stdin
    while True:
        try:
            # Read a line from stdin
            line = sys.stdin.readline().strip()
            if not line:
                continue
            
            # Parse the JSON-RPC request
            try:
                request = json.loads(line)
                
                # Process the request
                logger.info(f"processing started .....")
                response, should_exit = await server.process_request(request)
                logger.info(f"processing ended .....{response}")
                
                # Send the response
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
                
                # Exit if requested
                if should_exit:
                    logger.info("Shutting down...")
                    break
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                # Send error response for invalid JSON
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {e}"
                    },
                    "id": None
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            # Send error response
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                },
                "id": None
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())