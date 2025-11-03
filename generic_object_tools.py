"""
Generic Object Tools for OpenPages MCP Server
Provides tools for working with any object type in OpenPages
"""

import logging
import json
import urllib.parse
from typing import Any, Dict, List, Optional

from mcp.types import TextContent  # type: ignore

from openpages_client import OpenPagesClient
from base_tool import BaseTool

# Configure logging
logger = logging.getLogger(__name__)

class GenericObjectTools(BaseTool):
    """
    Tools for working with any object type in OpenPages
    
    This class provides object-centric tools for working with any object type in OpenPages,
    including finding, creating, updating, and deleting objects.
    """
    
    def __init__(self, client: OpenPagesClient, object_config: Dict[str, Any]):
        """
        Initialize generic object tools
        
        Args:
            client: OpenPages API client
            object_config: Configuration for the object type
        """
        super().__init__(client)
        self.object_config = object_config
        self.type_id = object_config.get("type_id", "")
        self.display_name = object_config.get("display_name", "Object")
        self.path_prefix = object_config.get("path_prefix", "")
        self.status_field = object_config.get("status_field", "")
        
    async def get_object_fields(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Get available fields for object creation
        
        Args:
            arguments: Tool arguments
                - object_type: Type of object (optional, defaults to configured type_id)
                
        Returns:
            List of text content with available fields information
        """
        object_type = arguments.get('object_type', self.type_id)
        
        try:
            # Get the type definition using the base class method
            type_info = await self.get_type_definition(object_type)
            
            # Extract field definitions
            field_definitions = type_info.get('field_definitions', [])
            
            if not field_definitions:
                return [TextContent(type="text", text=f"No fields found for {self.display_name.lower()} type: {object_type}")]
            
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
    
    async def create_object(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Create a new object in OpenPages
        
        Args:
            arguments: Tool arguments
                - name: Name of the object (required)
                - title: Object title (optional)
                - description: Description of the object (optional)
                - Any other field defined in the schema (optional)
                
        Returns:
            List of text content with created object information
        """
        # Extract required fields
        name = arguments.get('name')
        if not name:
            return [TextContent(type="text", text=f"Error: {self.display_name} name is required")]
        
        # Extract common fields
        primaryParentId = arguments.get('primaryParentId', '')
        title = arguments.get('title', '')
        description = arguments.get('description', '')
        
        # If primaryParentId is provided and not a number, resolve it using the utility function
        if primaryParentId and not primaryParentId.isdigit():
            logger.info(f"primaryParentId appears to be a path: {primaryParentId}")
            primaryParentId = await self.resolve_path_to_id(primaryParentId)
        
        # Prepare content data
        content_data: dict[str, Any] = {
            "name": name,
            "primary_parent_id": primaryParentId,
            "title": title,
            "description": description,
            "fields": [],
            "type_definition_id": self.type_id
        }
        
        # Get field definitions to properly format field values
        try:
            # Use base class method to get type definition
            type_info = await self.get_type_definition(self.type_id)
            field_definitions = type_info.get('field_definitions', [])
            
            # Create mappings for field names and labels
            field_def_map = {}  # Maps field names to definitions (case-sensitive)
            field_def_map_lower = {}  # Maps lowercase field names to definitions (case-insensitive)
            label_to_field_map = {}  # Maps lowercase labels to field names
            simple_name_map = {}  # Maps lowercase simple names to field names
            conflict_map = {}  # Tracks potential conflicts
            
            for field_def in field_definitions:
                field_name = field_def.get('name')
                if field_name:
                    # 1. Map full field name to definition (case-sensitive)
                    field_def_map[field_name] = field_def
                    
                    # Also map lowercase version for case-insensitive matching
                    field_name_lower = field_name.lower()
                    if field_name_lower in field_def_map_lower:
                        conflict_map[field_name_lower] = True
                        logger.warning(f"Field name conflict: '{field_name_lower}' maps to multiple fields")
                    field_def_map_lower[field_name_lower] = field_def
                    
                    # 2. Get user-friendly label and map it to field name (case-insensitive)
                    label = field_def.get('localized_label')
                    if label:
                        label_lower = label.lower()
                        if label_lower in label_to_field_map:
                            conflict_map[label_lower] = True
                            logger.warning(f"Label conflict: '{label}' maps to both '{label_to_field_map[label_lower]}' and '{field_name}'")
                        else:
                            label_to_field_map[label_lower] = field_name
                    
                    # 3. Map simple name (without prefix) to field name (case-insensitive)
                    simple_name = field_name.split(':')[-1] if ':' in field_name else field_name
                    simple_name_lower = simple_name.lower()
                    if simple_name_lower in simple_name_map:
                        conflict_map[simple_name_lower] = True
                        logger.warning(f"Simple name conflict: '{simple_name}' maps to both '{simple_name_map[simple_name_lower]}' and '{field_name}'")
                    else:
                        simple_name_map[simple_name_lower] = field_name
            
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
                field_name = None
                arg_name_lower = arg_name.lower()
                
                # 1. First try direct match with full field name (case-sensitive)
                if arg_name in field_def_map:
                    field_def = field_def_map[arg_name]
                    field_name = arg_name
                    logger.debug(f"Field '{arg_name}' matched by exact name")
                
                # 2. Try case-insensitive match with full field name
                elif arg_name_lower in field_def_map_lower:
                    # Check if this is a conflicted field name
                    if arg_name_lower in conflict_map:
                        logger.warning(f"Using ambiguous field name: '{arg_name}' has multiple possible matches")
                        # In case of conflict, prefer the exact match if available
                        for actual_name in field_def_map:
                            if actual_name.lower() == arg_name_lower:
                                field_name = actual_name
                                field_def = field_def_map[actual_name]
                                logger.debug(f"Ambiguous field '{arg_name}' resolved to exact match '{field_name}'")
                                break
                        # If no exact match found, use the first one
                        if not field_name:
                            field_def = field_def_map_lower[arg_name_lower]
                            field_name = field_def.get('name')
                            logger.debug(f"Ambiguous field '{arg_name}' using first match '{field_name}'")
                    else:
                        field_def = field_def_map_lower[arg_name_lower]
                        field_name = field_def.get('name')
                        logger.debug(f"Field '{arg_name}' matched by case-insensitive name to '{field_name}'")
                
                # 3. Try match with user-friendly label (case-insensitive)
                elif arg_name_lower in label_to_field_map:
                    if arg_name_lower in conflict_map:
                        logger.warning(f"Ambiguous label: '{arg_name}' could refer to multiple fields")
                    field_name = label_to_field_map[arg_name_lower]
                    field_def = field_def_map.get(field_name)
                    logger.debug(f"Field '{arg_name}' matched by label to '{field_name}'")
                
                # 4. Try match with simple name (without prefix) (case-insensitive)
                elif arg_name_lower in simple_name_map:
                    if arg_name_lower in conflict_map:
                        logger.warning(f"Ambiguous simple name: '{arg_name}' could refer to multiple fields")
                    field_name = simple_name_map[arg_name_lower]
                    field_def = field_def_map.get(field_name)
                    logger.debug(f"Field '{arg_name}' matched by simple name to '{field_name}'")
                
                if field_def:
                    field_name = field_def.get('name')
                    field_type = field_def.get('data_type', 'STRING_TYPE')
                    
                    # Format the value based on field type using base class method
                    formatted_value = self.format_field_value(arg_value, field_type)
                    
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
                
        except Exception as e:
            logger.error(f"Error processing field definitions: {e}")
            # Continue with basic fields if there's an error
        
        try:
            # Create the object
            logger.info(f"Creating new {self.display_name.lower()}: {content_data}")
            result = await self.client.create_content(content_data)
            
            # Extract resource ID from the result
            resource_id = result.get("id")
            if not resource_id:
                return [TextContent(type="text", text=f"Error: Failed to create {self.display_name.lower()} (no resource ID returned)")]
            
            # Use base class method to create response text
            response_items = {
                "Name": name,
                "Resource ID": resource_id,
                "Type": self.type_id,
                "Parent": primaryParentId,
                "Task-View Path": self.get_task_view_url(resource_id)
            }
            
            if description:
                response_items["Description"] = description
                
            response_text = self.create_response_text(f"Successfully created {self.display_name.lower()}:", response_items)
            
            return [TextContent(type="text", text=response_text)]
        
        except Exception as e:
            logger.error(f"Error creating {self.display_name.lower()}: {e}")
            return [TextContent(type="text", text=f"Error creating {self.display_name.lower()}: {str(e)}")]
    
    async def query_objects(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Query for objects in OpenPages
        
        Args:
            arguments: Tool arguments
                - name: Filter objects by name (partial match, optional)
                - owner_filter: Filter by current user ownership (default: False)
                - status_filter: Filter objects by status (optional)
                - limit: Maximum number of objects to return (default: 20)
                - sort_by: Field to sort by (default: "Name")
                - sort_order: Sort order, "ASC" or "DESC" (default: "ASC")
                - fields: List of additional fields to include in the output (optional, multiselect)
                  Resource ID, Name, Description, and Status are always included
                - fetch_all_properties: Whether to fetch all main properties (default: False)
                
        Returns:
            List of text content with objects information
        """
        name_filter = arguments.get('name')
        owner_filter = arguments.get('owner_filter', False)
        status_filter = arguments.get('status_filter')
        limit = arguments.get('limit', 20)
        sort_by = arguments.get('sort_by', [{'field': 'Name', 'order': 'ASC'}])
        fetch_all_properties = arguments.get('fetch_all_properties', False)
        
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
        required_fields = ['[Resource ID]', '[Name]', '[Description]']
        if self.status_field:
            required_fields.append(f'[{self.status_field}]')
        
        # Add additional fields if specified
        selected_fields = required_fields.copy()
        
        # Try to get field definitions to build a more complete mapping
        try:
            # Use base class method to get type definition
            type_info = await self.get_type_definition(self.type_id)
            field_definitions = type_info.get('field_definitions', [])
            
            # Use base class method to create field mapping
            field_mapping = self.create_field_mapping(field_definitions)
            
            # If fetch_all_properties is True, add all fields from the type definition
            if fetch_all_properties:
                for field_def in field_definitions:
                    field_name = field_def.get('name')
                    if field_name and not field_def.get('read_only', False):
                        sql_field = f'[{field_name}]'
                        if sql_field not in selected_fields:
                            selected_fields.append(sql_field)
        except Exception as e:
            logger.warning(f"Could not fetch field definitions: {e}. Using default field mapping.")
            field_mapping = {}
        
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
        FROM [{self.type_id}]
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
        
        if status_filter and self.status_field:
            query += f" AND [{self.status_field}] = '{status_filter}'"
            
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
        
        logger.info(f"Executing query for {self.display_name.lower()}s: {query}")
        result = await self.client.query(query)
        
        # Format results
        objects = []
        for row in result.get('rows', []):
            object_data = {}
            for field in row['fields']:
                # Handle case where field['value'] could be null
                if 'value' in field:
                    object_data[field['name']] = field['value']
                else:
                    object_data[field['name']] = None
            objects.append(object_data)
        
        # Create response
        if not objects:
            return [TextContent(type="text", text=f"No {self.display_name.lower()}s found matching the criteria.")]
        
        response_text = f"Found {len(objects)} {self.display_name.lower()}(s):\n\n"
        
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
        if self.status_field:
            display_names[self.status_field] = 'Status'
        
        for obj in objects:
            response_text += f"## {obj.get('Name', 'N/A')}\n"
            
            # Create a dictionary for the object items to display
            object_items = {}
            
            # Get the resource ID
            resource_id = obj.get('Resource ID', 'N/A')
            
            # Always show required fields first
            object_items["ID"] = resource_id
            
            # Add taskview link
            if resource_id != 'N/A':
                object_items["Task-View Path"] = self.get_task_view_url(resource_id)
            
            # Status might be returned with different field names depending on the query
            if self.status_field:
                status_value = obj.get('Status', obj.get(self.status_field, 'N/A'))
                object_items["Status"] = status_value
            
            # Add description if available
            description = obj.get('Description')
            if description:
                object_items["Description"] = description
            
            # Add all other available fields that were selected
            for field_name, field_value in obj.items():
                # Skip fields we've already handled
                if field_name in ['Resource ID', 'Name', 'Description']:
                    continue
                
                # Get display name for the field
                display_name = display_names.get(field_name, field_name)
                object_items[display_name] = field_value
            
            # Use base class method to format the object items
            for key, value in object_items.items():
                display_value = self.extract_display_value(value)
                response_text += f"- **{key}**: {display_value}\n"
            
            response_text += "\n"
        
        return [TextContent(type="text", text=response_text)]
    
    async def update_object(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Update an existing object in OpenPages
        
        Args:
            arguments: Tool arguments
                - resource_id: Resource ID of the object to update
                - path: Path of the object including the name (i.e. /High Oaks Bank/Africa and Middle East/Test Object #1)
                - name: Name of the object (optional)
                - title: Object title (optional)
                - description: Description of the object (optional)
                - Any other field defined in the schema (optional)
                
        Returns:
            List of text content with updated object information
        """
        # Extract required fields
        resource_id = arguments.get('resource_id')
        path = arguments.get('path')
        
        if not resource_id and not path:
            return [TextContent(type="text", text=f"Error: Resource ID or path is required")]
        
        if resource_id and path:
            return [TextContent(type="text", text=f"Error: Only one of resource ID or path is required")]

        name = arguments.get('name')
        if not name:
            return [TextContent(type="text", text=f"Error: {self.display_name} name is required")]
        
        object_id = resource_id
        if not object_id:
            object_id = f"{self.path_prefix}/{path}"
            object_id = urllib.parse.quote(object_id, safe='')
            
        # Extract common fields
        title = arguments.get('title')
        description = arguments.get('description')
        
        # Prepare content data
        content_data: dict[str, Any] = {
            "fields": [],
            "type_definition_id": self.type_id
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
            # Use base class method to get type definition
            type_info = await self.get_type_definition(self.type_id)
            field_definitions = type_info.get('field_definitions', [])
            
            # Create mappings for field names and labels
            field_def_map = {}  # Maps field names to definitions (case-sensitive)
            field_def_map_lower = {}  # Maps lowercase field names to definitions (case-insensitive)
            label_to_field_map = {}  # Maps lowercase labels to field names
            simple_name_map = {}  # Maps lowercase simple names to field names
            conflict_map = {}  # Tracks potential conflicts
            
            for field_def in field_definitions:
                field_name = field_def.get('name')
                if field_name:
                    # 1. Map full field name to definition (case-sensitive)
                    field_def_map[field_name] = field_def
                    
                    # Also map lowercase version for case-insensitive matching
                    field_name_lower = field_name.lower()
                    if field_name_lower in field_def_map_lower:
                        conflict_map[field_name_lower] = True
                        logger.warning(f"Field name conflict: '{field_name_lower}' maps to multiple fields")
                    field_def_map_lower[field_name_lower] = field_def
                    
                    # 2. Get user-friendly label and map it to field name (case-insensitive)
                    label = field_def.get('localized_label')
                    if label:
                        label_lower = label.lower()
                        if label_lower in label_to_field_map:
                            conflict_map[label_lower] = True
                            logger.warning(f"Label conflict: '{label}' maps to both '{label_to_field_map[label_lower]}' and '{field_name}'")
                        else:
                            label_to_field_map[label_lower] = field_name
                    
                    # 3. Map simple name (without prefix) to field name (case-insensitive)
                    simple_name = field_name.split(':')[-1] if ':' in field_name else field_name
                    simple_name_lower = simple_name.lower()
                    if simple_name_lower in simple_name_map:
                        conflict_map[simple_name_lower] = True
                        logger.warning(f"Simple name conflict: '{simple_name}' maps to both '{simple_name_map[simple_name_lower]}' and '{field_name}'")
                    else:
                        simple_name_map[simple_name_lower] = field_name
            
            # Process all arguments and map them to OpenPages fields
            for arg_name, arg_value in arguments.items():
                # Skip special fields that are handled separately
                if arg_name in ['name', 'title', 'description', 'resource_id', 'path']:
                    continue
                    
                # Skip empty values
                if arg_value is None or arg_value == '':
                    continue
                
                # Try to find the matching field definition
                field_def = None
                field_name = None
                arg_name_lower = arg_name.lower()
                
                # 1. First try direct match with full field name (case-sensitive)
                if arg_name in field_def_map:
                    field_def = field_def_map[arg_name]
                    field_name = arg_name
                    logger.debug(f"Field '{arg_name}' matched by exact name")
                
                # 2. Try case-insensitive match with full field name
                elif arg_name_lower in field_def_map_lower:
                    # Check if this is a conflicted field name
                    if arg_name_lower in conflict_map:
                        logger.warning(f"Using ambiguous field name: '{arg_name}' has multiple possible matches")
                        # In case of conflict, prefer the exact match if available
                        for actual_name in field_def_map:
                            if actual_name.lower() == arg_name_lower:
                                field_name = actual_name
                                field_def = field_def_map[actual_name]
                                logger.debug(f"Ambiguous field '{arg_name}' resolved to exact match '{field_name}'")
                                break
                        # If no exact match found, use the first one
                        if not field_name:
                            field_def = field_def_map_lower[arg_name_lower]
                            field_name = field_def.get('name')
                            logger.debug(f"Ambiguous field '{arg_name}' using first match '{field_name}'")
                    else:
                        field_def = field_def_map_lower[arg_name_lower]
                        field_name = field_def.get('name')
                        logger.debug(f"Field '{arg_name}' matched by case-insensitive name to '{field_name}'")
                
                # 3. Try match with user-friendly label (case-insensitive)
                elif arg_name_lower in label_to_field_map:
                    if arg_name_lower in conflict_map:
                        logger.warning(f"Ambiguous label: '{arg_name}' could refer to multiple fields")
                    field_name = label_to_field_map[arg_name_lower]
                    field_def = field_def_map.get(field_name)
                    logger.debug(f"Field '{arg_name}' matched by label to '{field_name}'")
                
                # 4. Try match with simple name (without prefix) (case-insensitive)
                elif arg_name_lower in simple_name_map:
                    if arg_name_lower in conflict_map:
                        logger.warning(f"Ambiguous simple name: '{arg_name}' could refer to multiple fields")
                    field_name = simple_name_map[arg_name_lower]
                    field_def = field_def_map.get(field_name)
                    logger.debug(f"Field '{arg_name}' matched by simple name to '{field_name}'")
                
                if field_def:
                    field_name = field_def.get('name')
                    field_type = field_def.get('data_type', 'STRING_TYPE')
                    
                    # Format the value based on field type using base class method
                    formatted_value = self.format_field_value(arg_value, field_type)
                    
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
                    
        except Exception as e:
            logger.error(f"Error processing field definitions: {e}")
            # Continue with basic fields if there's an error
        
        try:
            # Update the object
            logger.info(f"Updating {self.display_name.lower()} {object_id}: {content_data}")
            result = await self.client.update_content(object_id, content_data)
            
            # Extract resource ID from the result
            updated_resource_id = result.get("id")
            if not updated_resource_id:
                return [TextContent(type="text", text=f"Error: Failed to update {self.display_name.lower()} (no resource ID returned)")]
            
            # Use base class method to create response text
            response_items = {
                "Resource ID": updated_resource_id,
                "Task-View Path": self.get_task_view_url(updated_resource_id)
            }
            
            if name:
                response_items["Name"] = name
                
            if description:
                response_items["Description"] = description
                
            response_text = self.create_response_text(f"Successfully updated {self.display_name.lower()}:", response_items)
            
            return [TextContent(type="text", text=response_text)]
        
        except Exception as e:
            logger.error(f"Error updating {self.display_name.lower()}: {e}")
            return [TextContent(type="text", text=f"Error updating {self.display_name.lower()}: {str(e)}")]
    
    async def delete_object(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Delete an existing object in OpenPages
        
        Args:
            arguments: Tool arguments
                - resource_id: Resource ID of the object to delete
                - path: Path of the object including the name (i.e. /High Oaks Bank/Africa and Middle East/Test Object #1)
                
        Returns:
            List of text content with deletion confirmation
        """
        # Extract required fields
        resource_id = arguments.get('resource_id')
        path = arguments.get('path')
        
        if not resource_id and not path:
            return [TextContent(type="text", text=f"Error: Resource ID or path is required")]
        
        if resource_id and path:
            return [TextContent(type="text", text=f"Error: Only one of resource ID or path is required")]
        
        object_id = resource_id
        if not object_id:
            object_id = f"{self.path_prefix}/{path}"
            object_id = urllib.parse.quote(object_id, safe='')
        
        try:
            # Get object details before deletion for confirmation message
            object_info = {}
            try:
                object_data = await self.client.get_content(object_id)
                if object_data:
                    object_info = {
                        "Name": object_data.get("name", "Unknown"),
                        "Resource ID": object_data.get("id", object_id)
                    }
            except Exception as e:
                logger.warning(f"Could not retrieve {self.display_name.lower()} details before deletion: {e}")
                # Continue with deletion even if we couldn't get details
            
            # Delete the object
            logger.info(f"Deleting {self.display_name.lower()} with ID: {object_id}")
            result = await self.client.delete_content(object_id)
            
            # Create response text
            if object_info:
                response_items = object_info
            else:
                response_items = {"Resource ID": object_id}
                
            response_text = self.create_response_text(f"Successfully deleted {self.display_name.lower()}:", response_items)
            
            return [TextContent(type="text", text=response_text)]
        
        except Exception as e:
            logger.error(f"Error deleting {self.display_name.lower()}: {e}")
            return [TextContent(type="text", text=f"Error deleting {self.display_name.lower()}: {str(e)}")]

# Made with Bob
