# OpenPages MCP Server - Langflow Integration Guide

This guide provides step-by-step instructions for integrating the OpenPages MCP Server with Langflow to create AI-powered agentic workflows for IBM OpenPages GRC operations.

## Overview

Langflow is an open-source visual framework for building AI applications with a drag-and-drop interface. By integrating the OpenPages MCP Server with Langflow, you can create powerful AI agents that interact with OpenPages to manage Issues, Controls, Risks, and other GRC entities through natural language conversations.

## Prerequisites

1. **OpenPages Instance**: Access to an IBM OpenPages instance (SaaS or on-premises) with valid credentials
2. **Python 3.11+**: Required for running the MCP server
3. **Langflow**: Installed and running (see [Langflow documentation](https://docs.langflow.org/))
4. **Node.js** (Optional): For testing with MCP Inspector

## Setup Instructions

### Step 1: Download and Setup the OpenPages MCP Server

Clone the repository to a new folder:

```bash
mkdir openpages-mcp-demo
cd openpages-mcp-demo
git clone https://github.com/IBM/ibm-openpages-local-mcp-server.git
cd ibm-openpages-local-mcp-server
```

### Step 2: Configure Environment Variables

Create a `.env` file from the example template:

```bash
cp .env.example .env
```

Open the `.env` file in your preferred text editor (e.g., VS Code):

```bash
code .
```

Configure the following required values for your OpenPages instance:

#### For SaaS Deployments (IBM Cloud or MCSP):
```env
OPENPAGES_BASE_URL=https://your-instance.openpages.ibmcloud.com
OPENPAGES_AUTHENTICATION_TYPE=bearer
OPENPAGES_APIKEY=your_api_key_here

# For IBM Cloud:
OPENPAGES_AUTHENTICATION_URL=https://iam.cloud.ibm.com/identity/token

# For MCSP:
# OPENPAGES_AUTHENTICATION_URL=https://account-iam.platform.saas.ibm.com/api/2.0/services/{service_id}/apikeys/token

SSL_VERIFY=True
```

#### For On-Premises Deployments:
```env
OPENPAGES_BASE_URL=https://your-openpages-server.com
OPENPAGES_AUTHENTICATION_TYPE=basic
OPENPAGES_USERNAME=your_username
OPENPAGES_PASSWORD=your_password

# For local development environments:
SSL_VERIFY=False
```

### Step 3: Create Python Virtual Environment

Create and activate a Python virtual environment, then install dependencies:

#### On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 4: Optional - Test with MCP Inspector

Before integrating with Langflow, test the MCP server using the MCP Inspector to verify your configuration:

Start the MCP Inspector:
```bash
npx @modelcontextprotocol/inspector@latest
```

The MCP Inspector UI will open in your browser. Configure it with the following settings:
- **Transport Type**: STDIO
- **Command**: `python` (or full path to your virtual environment's Python: `/path/to/venv/bin/python`)
- **Arguments**: `start_mcp.py`

Click "Connect" to start the MCP server. The MCP Inspector provides a web UI where you can:
- View all available tools
- Test tool execution with sample inputs
- Verify OpenPages connectivity
- Debug any configuration issues

### Step 5: Create an Agentic Flow in Langflow

1. Open Langflow app
2. Create a new flow by clicking "New Flow"
3. Add the following components to your flow:
   - **Chat Input**: For receiving user queries
   - **Agent**: The main orchestrator component
   - **MCP Server**: The OpenPages MCP server connector
   - **LLM Model**: Your preferred language model
   - **Chat Output**: For displaying agent responses

4. Connect the components as given below:
   <img width="970" height="671" alt="image" src="https://github.com/user-attachments/assets/35eedecc-e3af-47c3-98be-268ad50e6f23" />


   

### Step 6: Configure the LLM Model

Add and configure your LLM model in Langflow. Here are examples for common providers:

#### Azure OpenAI:
- **Model Provider**: Azure OpenAI
- **Deployment Name**: Your Azure deployment name (e.g., `gpt-4`)
- **API Base**: Your Azure OpenAI endpoint (e.g., `https://your-resource.openai.azure.com/`)
- **API Key**: Your Azure OpenAI API key
- **API Version**: `2024-02-15-preview` or latest
- **Temperature**: `0.7` (recommended for balanced responses)

#### OpenAI:
- **Model Provider**: OpenAI
- **Model Name**: `gpt-4`, `gpt-4o`, or `gpt-3.5-turbo`
- **API Key**: Your OpenAI API key
- **Temperature**: `0.7`

#### IBM watsonx.ai:
- **Model Provider**: IBM watsonx.ai
- **Model ID**: `ibm/granite-13b-chat-v2` or other supported models
- **API Key**: Your IBM Cloud API key
- **Project ID**: Your watsonx.ai project ID

### Step 7: Add the OpenPages MCP Server to Langflow

Configure the MCP Server component in Langflow with the following settings:

#### Python Executable Path:
Point to the Python executable in your virtual environment:

**Format:**
```
<PATH_TO_PROJECT>/venv/bin/python
```

#### MCP Server Script Path:
Point to the start_mcp.py script with the --env-file parameter:

**Format:**
```
<PATH_TO_PROJECT>/start_mcp.py --env-file <PATH_TO_PROJECT>/.env
```

### Step 8: Configure Agent Instructions

Add the following instructions to your Langflow agent component to ensure proper handling of OpenPages operations:

```
You are a helpful assistant that can use tools to answer questions and perform tasks.

For OpenPages operations:
- Use openpages-mcp-tools:create_issue, update_issue, query_issues for issue management
- Use openpages-mcp-tools:create_control, update_control, query_controls for control management
- Use openpages-mcp-tools:create_risk, update_risk, query_risks for risk management
- Format user input according to tool schema requirements
- The create and update tools support passing all properties, so pass the field technical name to the tool as given by the user
- In the create tool, pass all the fields given by user, and don't try to do create first with basic fields and then do another update. Try to do the operation in a single tool call, if possible

Field name handling when working with OpenPages fields:

1. Field Naming Conventions:
   - Full technical field name: The complete identifier with prefix (e.g., "OPSS-Ctl:Status")
   - User-friendly label: The human-readable name (e.g., "Status") found in the schema as x-label
   - Simple name: The field name without prefix (e.g., "Status")

2. Field Name Resolution:
   - Users will typically provide the user-friendly label
   - Always convert user-provided labels to the appropriate full technical field name when passing to MCP tools
   - Use the following resolution order:
     a. Exact match with full technical field name
     b. Case-insensitive match with full technical field name
     c. Match with user-friendly label
     d. Match with simple name (without prefix)

3. Handling Ambiguity:
   - If a label is ambiguous (could refer to multiple fields):
     a. Inform the user about the ambiguity
     b. List the possible full technical field names that match
     c. Ask the user to specify which full technical field name they want to use
   - Example: "The label 'Status' is ambiguous and could refer to multiple fields: 'OPSS-Ctl:Status' or 'OPSS-Iss:Status'. Please specify which field you want to use."

4. Feedback:
   - When resolving field names, provide transparent feedback about which technical field is being used
   - Example: "Using field 'OPSS-Ctl:Status' for the label 'Status'"
```

### Step 9: Test the Integration

Test your Langflow integration with the following example prompts. 

**Important:** Replace the `Primary parent id` and `Issue Owner` values with valid values from your OpenPages environment before testing.

#### Example 1: Create an Issue

```
Create an issue in OpenPages with the following details:
Name - Issue for business Entity ABC Ltd
Description - Mitigating infra risks
Primary parent id - 8366
Issue Owner - jayasankar.sreedharan@ibm.com
Priority - Medium
Issue Status - Open
Issue Type - Design Effectiveness

Use all the fields given above for creating the issue
```

**Expected Result:** The agent should create a new risk with all specified properties.

## Troubleshooting

### Issue: MCP Server Not Connecting

**Symptoms:**
- Langflow shows "MCP server connection failed"
- Tools are not available in the agent

**Solutions:**
1. Verify the Python executable path points to your virtual environment's Python:
   ```bash
   # Test the path
   /path/to/venv/bin/python --version
   ```

2. Ensure the start_mcp.py script path is correct and includes the --env-file parameter

3. Check that the .env file exists and contains valid OpenPages credentials

4. Review the Langflow logs for specific error messages

### Issue: Tools Not Available

**Symptoms:**
- Agent doesn't recognize OpenPages tools
- "Tool not found" errors

**Solutions:**
1. Restart the Langflow flow to reload the MCP server
2. Check the MCP server logs for any startup errors
3. Verify that `object_types.json` is present in the server directory
4. Test the server independently using MCP Inspector

### Issue: Authentication Errors

**Symptoms:**
- "401 Unauthorized" or "403 Forbidden" errors
- "Invalid credentials" messages

**Solutions:**
1. Verify your OpenPages credentials in the .env file
2. For SaaS deployments:
   - Ensure you're using `bearer` authentication
   - Verify your API key is valid and has OpenPages access
   - Check the authentication URL is correct for your deployment (IBM Cloud vs MCSP)
3. For on-premises deployments:
   - Ensure you're using `basic` authentication
   - Verify username and password are correct
   - Check if SSL_VERIFY should be False for local development

### Issue: Field Name Errors

**Symptoms:**
- "Invalid field name" errors
- Fields not being set correctly

**Solutions:**
1. Ensure you're using the correct technical field names (e.g., "OPSS-Iss:Status" not just "Status")
2. Check the OpenPages schema for the exact field names:
   - Use the query tools to see available fields
   - Review the tool schema in MCP Inspector
3. Verify field values match the allowed values in OpenPages (e.g., enum values)

### Issue: SSL Certificate Errors

**Symptoms:**
- "SSL certificate verification failed" errors
- Connection timeout errors

**Solutions:**
1. For production/SaaS environments:
   - Set `SSL_VERIFY=True` in .env
   - Ensure your system has up-to-date CA certificates
2. For local development environments:
   - Set `SSL_VERIFY=False` in .env (not recommended for production)


## Advanced Configuration

### Custom Object Types

To add support for additional OpenPages object types, edit the `object_types.json` file:

```json
{
  "object_types": [
    {
      "type_id": "SOXAction",
      "tool_prefix": "action",
      "display_name": "Action",
      "path_prefix": "Actions",
      "status_field": "OPSS-Act:Status"
    }
  ]
}
```

After adding new object types, restart the MCP server for changes to take effect.


### Custom Agent Behaviors

Extend the agent instructions to handle specific use cases:


## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
