"""
Control Tools for OpenPages MCP Server
Provides tools for working with controls in OpenPages
"""

import logging
import json
from typing import Any, Dict, List, Optional

from mcp.types import TextContent  # type: ignore

from openpages_client import OpenPagesClient

# Configure logging
logger = logging.getLogger(__name__)

class ControlTools:
    """
    Tools for working with controls in OpenPages
    
    This class provides object-centric tools for working with Controls objects in OpenPages,
    including finding, creating, and updating controls.
    """
    
    def __init__(self, client: OpenPagesClient):
        """
        Initialize control tools
        
        Args:
            client: OpenPages API client
        """
        self.client = client
        
    async def get_control_fields(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Get available fields for control creation
        
        Args:
            arguments: Tool arguments
                - control_type: Type of control (default: SOXControl)
                
        Returns:
            List of text content with available fields information
        """
        object_type = arguments.get('control_type', 'SOXControl')
        
        try:
            # Get the type definition using the client's method
            logger.info(f"Fetching type definition for: {object_type}")
            type_info = await self.client.get_type_definition(object_type)
            
            # Extract field definitions
            field_definitions = type_info.get('field_definitions', [])
            
            if not field_definitions:
                return [TextContent(type="text", text=f"No fields found for control type: {object_type}")]
            
            # Format the response
            response_text = f"Available fields for {object_type} (ID: {type_info.get('id')}):\n\n"
            response_text += f"Display Name: {type_info.get('localized_label', type_info.get('name'))}\n"
            response_text += f"Description: {type_info.get('description', 'No description available')}\n\n"
            response_text += "## Available Fields:\n\n"
            
            # Sort fields by name for better readability
            field_definitions.sort(key=lambda x: x.get('name', ''))
            
            for field in field_definitions:
                field_name = field.get('name', 'N/A')
                field_type = field.get('data_type', 'N/A')
                description = field.get('description', 'No description available')
                required = "Required" if field.get('required', False) else "Optional"
                read_only = "Read-only" if field.get('read_only', False) else "Editable"
                
                # Add enum values if available
                enum_values = field.get('enum_values', [])
                enum_text = ""
                if enum_values and field_type == "ENUM_TYPE":
                    enum_text = "\n    Allowed values: " + ", ".join([f"'{v.get('name')}'" for v in enum_values])
                
                response_text += f"- **{field_name}** ({field_type}): {description} [{required}, {read_only}]{enum_text}\n\n"
            
            return [TextContent(type="text", text=response_text)]
                
        except Exception as e:
            logger.error(f"Error getting field definitions: {e}")
            return [TextContent(type="text", text=f"Error retrieving field definitions: {str(e)}")]
    
    async def create_control(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Create a new control in OpenPages
        
        Args:
            arguments: Tool arguments
                - name: Name of the control (required)
                - title: Control title (optional)
                - description: Description of the control (optional)
                - Any other field defined in the schema (optional)
                
        Returns:
            List of text content with created control information
        """
        # Extract required fields
        name = arguments.get('name')
        if not name:
            return [TextContent(type="text", text="Error: Control name is required")]
        
        # Extract common fields
        primaryParentId = arguments.get('primaryParentId', '')
        title = arguments.get('title', '')
        description = arguments.get('description', '')
        control_type = "SOXControl"
        
        # Prepare content data
        content_data: dict[str, Any] = {
            "name": name,
            "primary_parent_id": primaryParentId,
            "title": title,
            "description": description,
            "fields": [],
            "type_definition_id": control_type
        }
        
        # Get field definitions to properly format field values
        try:
            type_info = await self.client.get_type_definition(control_type)
            field_definitions = type_info.get('field_definitions', [])
            
            # Create a mapping of field names to their definitions for easy lookup
            field_def_map = {}
            for field_def in field_definitions:
                field_name = field_def.get('name')
                if field_name:
                    field_def_map[field_name] = field_def
                    
                    # Also map the field name without the prefix for easier matching
                    simple_name = field_name.split(':')[-1] if ':' in field_name else field_name
                    field_def_map[simple_name.lower()] = field_def
            
            # Process all arguments and map them to OpenPages fields
            for arg_name, arg_value in arguments.items():
                # Skip special fields that are handled separately
                if arg_name in ['name', 'primaryParentId', 'title', 'description']:
                    continue
                    
                # Skip empty values
                if arg_value is None or arg_value == '':
                    continue
                
                # Try to find the matching field definition
                field_def = None
                
                # First try direct match
                if arg_name in field_def_map:
                    field_def = field_def_map[arg_name]
                # Then try lowercase match
                elif arg_name.lower() in field_def_map:
                    field_def = field_def_map[arg_name.lower()]
                
                if field_def:
                    field_name = field_def.get('name')
                    field_type = field_def.get('data_type', 'STRING_TYPE')
                    
                    # Format the value based on field type
                    formatted_value = arg_value
                    
                    # Handle enum types (need to be objects with name property)
                    if field_type == "ENUM_TYPE":
                        formatted_value = {"name": arg_value}
                    
                    # Add the field to the content data
                    content_data["fields"].append({
                        "name": field_name,
                        "value": formatted_value
                    })
                    logger.info(f"Added field {field_name} with value {formatted_value}")
                else:
                    # If no matching field definition found, add it as is
                    # This might happen for custom fields or if the field name doesn't match exactly
                    logger.warning(f"No field definition found for {arg_name}, adding as is")
                    content_data["fields"].append({
                        "name": arg_name,
                        "value": arg_value
                    })
            
            # No special handling for specific fields - all fields are processed in the loop above
                
        except Exception as e:
            logger.error(f"Error processing field definitions: {e}")
            # Continue with basic fields if there's an error
        
        try:
            # Create the control
            logger.info(f"Creating new control: {content_data}")
            result = await self.client.create_content(content_data)
            
            # Extract resource ID from the result
            resource_id = result.get("id")
            if not resource_id:
                return [TextContent(type="text", text="Error: Failed to create control (no resource ID returned)")]
            
            response_text = f"Successfully created control:\n\n"
            response_text += f"- **Name**: {name}\n"
            response_text += f"- **Resource ID**: {resource_id}\n"
            response_text += f"- **Type**: {control_type}\n"
            response_text += f"- **parent**: {primaryParentId}\n"
            
            if description:
                response_text += f"- **Description**: {description}\n"
            
            return [TextContent(type="text", text=response_text)]
        
        except Exception as e:
            logger.error(f"Error creating control: {e}")
            return [TextContent(type="text", text=f"Error creating control: {str(e)}")]
    
    async def query_controls(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Query for Controls in OpenPages
        
        Args:
            arguments: Tool arguments
                - name: Filter controls by name (partial match, optional)
                - owner_filter: Filter by current user ownership (default: False)
                # - status_filter: Filter controls by status (optional)
                - limit: Maximum number of controls to return (default: 20)
                - sort_by: Field to sort by (default: "Name")
                - sort_order: Sort order, "ASC" or "DESC" (default: "ASC")
                - fields: List of additional fields to include in the output (optional, multiselect)
                  Resource ID, Name, Description, and Status are always included
                
        Returns:
            List of text content with controls information
        """
        name_filter = arguments.get('name')
        owner_filter = arguments.get('owner_filter', False)
        # status_filter = arguments.get('status_filter')
        limit = arguments.get('limit', 20)
        sort_by = arguments.get('sort_by', [{'field': 'Name', 'order': 'ASC'}])
        
        # Handle backward compatibility
        if isinstance(sort_by, str):
            # Old format: single string field name with separate sort_order
            sort_order = arguments.get('sort_order', 'ASC')
            sort_fields = [{'field': sort_by, 'order': sort_order}]
        elif isinstance(sort_by, list) and all(isinstance(item, str) for item in sort_by):
            # Old format: list of field names with single sort_order
            sort_order = arguments.get('sort_order', 'ASC')
            sort_fields = [{'field': field, 'order': sort_order} for field in sort_by]
        else:
            # New format: list of objects with field and order
            sort_fields = sort_by
            
        # Limit to first 3 fields
        sort_fields = sort_fields[:3]
        additional_fields = arguments.get('fields', [])
        
        # Always include these required fields
        required_fields = ['[Resource ID]', '[Name]', '[Description]', '[OPSS-Ctl:Status]']
        
        # # Map common field names to their SQL column names
        field_mapping = {
            # 'Priority': '[OPSS-Iss:Priority]',
            # 'Owner': '[Owner]',
            # 'Due Date': '[OPSS-Iss:DueDate]',
            # 'Status': '[OPSS-Ctl:Status]'
        }
        
        # Add additional fields if specified
        selected_fields = required_fields.copy()
        
        # Try to get field definitions to build a more complete mapping
        try:
            type_info = await self.client.get_type_definition('SOXControl')
            field_definitions = type_info.get('field_definitions', [])
            
            # Update field mapping with all available fields from type definition
            for field_def in field_definitions:
                field_name = field_def.get('name')
                if field_name:
                    # Create a simplified name for easier matching
                    simple_name = field_name.split(':')[-1] if ':' in field_name else field_name
                    field_mapping[simple_name] = f'[{field_name}]'
        except Exception as e:
            logger.warning(f"Could not fetch field definitions: {e}. Using default field mapping.")
        
        # Process additional fields
        for field in additional_fields:
            # Check if the field is already in the required fields
            sql_field = None
            
            # Extract the field name without the group if present
            # Format is "Name [Group]"
            field_name = field
            if '[' in field and field.endswith(']'):
                field_name = field.split('[')[0].strip()
                group_name = field[field.find('[')+1:field.find(']')]
                
                # Try to find the full field name with group prefix
                full_field_name = f"{group_name}:{field_name}"
                if full_field_name in field_mapping:
                    sql_field = field_mapping[full_field_name]
                    
            # If not found with group, try direct match
            if not sql_field and field_name in field_mapping:
                sql_field = field_mapping[field_name]
            # Try case-insensitive match
            elif not sql_field and field_name.lower() in {k.lower(): v for k, v in field_mapping.items()}:
                for k, v in field_mapping.items():
                    if k.lower() == field_name.lower():
                        sql_field = v
                        break
                        
            if sql_field and sql_field not in selected_fields:
                selected_fields.append(sql_field)
        
        # Build query with selected fields
        query = f"""
        SELECT {', '.join(selected_fields)}
        FROM [SOXControl]
        WHERE [Resource ID] IS NOT NULL
        """
        
        # Add name filter if specified
        if name_filter:
            query += f" AND [Name] LIKE '%{name_filter}%'"
        
        # Add owner filter if requested
        if owner_filter:
            current_user = await self.client.get_current_user()
            if current_user:
                query += f" AND [Owner] = '{current_user}'"
        
        # if status_filter:
        #     query += f" AND [OPSS-Ctl:Status] = '{status_filter}'"
            
        # Add sorting with multiple fields
        sort_clauses = []
        for sort_item in sort_fields:
            field = sort_item['field']
            order = sort_item['order']
            
            # Handle field names with group information in brackets
            if isinstance(field, str) and '[' in field and field.endswith(']'):
                field_name = field.split('[')[0].strip()
                group_name = field[field.find('[')+1:field.find(']')]
                full_field_name = f"{group_name}:{field_name}"
                
                # Check if this field exists in field_mapping
                if full_field_name in field_mapping:
                    sort_clauses.append(f"{field_mapping[full_field_name]} {order}")
                else:
                    # Use the full field name with group prefix
                    sort_clauses.append(f"[{full_field_name}] {order}")
            else:
                sort_clauses.append(f"[{field}] {order}")
                
        query += f" ORDER BY {', '.join(sort_clauses)}" if sort_clauses else ""
        
        # Add limit
        query += f" LIMIT {limit}"
        
        logger.info(f"Executing query for controls: {query}")
        result = await self.client.query(query)
        
        # Format results
        controls = []
        for row in result.get('rows', []):
            control_data = {}
            for field in row['fields']:
                # Handle case where field['value'] could be null
                if 'value' in field:
                    control_data[field['name']] = field['value']
                else:
                    control_data[field['name']] = None
            controls.append(control_data)
        
        # Create response
        if not controls:
            return [TextContent(type="text", text="No controls found matching the criteria.")]
        
        response_text = f"Found {len(controls)} controls(s):\n\n"
        
        # Create a reverse mapping from SQL field names to display names
        display_names = {}
        for display_name, sql_field in field_mapping.items():
            # Remove brackets from SQL field name for matching with result keys
            clean_field = sql_field.replace('[', '').replace(']', '')
            display_names[clean_field] = display_name
            
        # Add special cases for required fields
        display_names['Resource ID'] = 'ID'
        display_names['Name'] = 'Name'
        display_names['Description'] = 'Description'
        # display_names['OPSS-Ctl:Status'] = 'Status'
        
        for control in controls:
            response_text += f"## {control.get('Name', 'N/A')}\n"
            
            # Always show required fields first
            response_text += f"- **ID**: {control.get('Resource ID', 'N/A')}\n"
            
            # Status might be returned with different field names depending on the query
            # status_value = control.get('Status', control.get('OPSS-Ctl:Status', 'N/A'))
            # # Handle enum types (objects with name property)
            # if isinstance(status_value, dict) and 'name' in status_value:
            #     status_value = status_value['name']
            # response_text += f"- **Status**: {status_value}\n"
            
            # Add description if available
            description = control.get('Description')
            if description:
                response_text += f"- **Description**: {description}\n"
            
            # Add all other available fields that were selected
            for field_name, field_value in control.items():
                # Skip fields we've already handled
                if field_name in ['Resource ID', 'Name', 'Description']:
                    continue
                    
                # Display fields even if they have null values
                if field_value is None or field_value == '':
                    field_value = 'N/A'
                
                # Handle enum types (objects with name property)
                if isinstance(field_value, dict) and 'name' in field_value:
                    field_value = field_value['name']
                
                # Get display name for the field
                display_name = display_names.get(field_name, field_name)
                response_text += f"- **{display_name}**: {field_value}\n"
            
            response_text += "\n"
        
        return [TextContent(type="text", text=response_text)]
    
    async def update_control(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Update an existing control in OpenPages
        
        Args:
            arguments: Tool arguments
                - resource_id: Resource ID of the control to update (required)
                - name: Name of the control (optional)
                - title: Control title (optional)
                - description: Description of the control (optional)
                - Any other field defined in the schema (optional)
                
        Returns:
            List of text content with updated control information
        """
        # Extract required fields
        resource_id = arguments.get('resource_id')
        if not resource_id:
            return [TextContent(type="text", text="Error: Resource ID is required")]
        
        # Extract common fields
        name = arguments.get('name')
        title = arguments.get('title')
        description = arguments.get('description')
        control_type = "SOXControl"
        
        # Prepare content data
        content_data: dict[str, Any] = {
            "fields": [],
            "type_definition_id": control_type
        }
        
        # Add optional fields if provided
        if name:
            content_data["name"] = name
        if title:
            content_data["title"] = title
        if description:
            content_data["description"] = description
        
        # Get field definitions to properly format field values
        try:
            type_info = await self.client.get_type_definition(control_type)
            field_definitions = type_info.get('field_definitions', [])
            
            # Create a mapping of field names to their definitions for easy lookup
            field_def_map = {}
            for field_def in field_definitions:
                field_name = field_def.get('name')
                if field_name:
                    field_def_map[field_name] = field_def
                    
                    # Also map the field name without the prefix for easier matching
                    simple_name = field_name.split(':')[-1] if ':' in field_name else field_name
                    field_def_map[simple_name.lower()] = field_def
            
            # Process all arguments and map them to OpenPages fields
            for arg_name, arg_value in arguments.items():
                # Skip special fields that are handled separately
                if arg_name in ['name', 'title', 'description', 'resource_id']:
                    continue
                    
                # Skip empty values
                if arg_value is None or arg_value == '':
                    continue
                
                # Try to find the matching field definition
                field_def = None
                
                # First try direct match
                if arg_name in field_def_map:
                    field_def = field_def_map[arg_name]
                # Then try lowercase match
                elif arg_name.lower() in field_def_map:
                    field_def = field_def_map[arg_name.lower()]
                
                if field_def:
                    field_name = field_def.get('name')
                    field_type = field_def.get('data_type', 'STRING_TYPE')
                    
                    # Format the value based on field type
                    formatted_value = arg_value
                    
                    # Handle enum types (need to be objects with name property)
                    if field_type == "ENUM_TYPE":
                        formatted_value = {"name": arg_value}
                    
                    # Add the field to the content data
                    content_data["fields"].append({
                        "name": field_name,
                        "value": formatted_value
                    })
                    logger.info(f"Added field {field_name} with value {formatted_value}")
                else:
                    # If no matching field definition found, add it as is
                    # This might happen for custom fields or if the field name doesn't match exactly
                    logger.warning(f"No field definition found for {arg_name}, adding as is")
                    content_data["fields"].append({
                        "name": arg_name,
                        "value": arg_value
                    })
            
            # No special handling for specific fields - all fields are processed in the loop above
                
        except Exception as e:
            logger.error(f"Error processing field definitions: {e}")
            # Continue with basic fields if there's an error
        
        try:
            # Update the control
            logger.info(f"Updating control {resource_id}: {content_data}")
            result = await self.client.update_content(resource_id, content_data)
            
            # Extract resource ID from the result
            updated_resource_id = result.get("id")
            if not updated_resource_id:
                return [TextContent(type="text", text="Error: Failed to update control (no resource ID returned)")]
            
            response_text = f"Successfully updated control:\n\n"
            response_text += f"- **Resource ID**: {updated_resource_id}\n"
            
            if name:
                response_text += f"- **Name**: {name}\n"
            
            if description:
                response_text += f"- **Description**: {description}\n"
            
            return [TextContent(type="text", text=response_text)]
        
        except Exception as e:
            logger.error(f"Error updating control: {e}")
            return [TextContent(type="text", text=f"Error updating control: {str(e)}")]