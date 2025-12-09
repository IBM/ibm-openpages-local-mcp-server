# OpenPages Local MCP Server

A local Model Context Protocol (MCP) server that enables AI agents to securely interact with IBM OpenPages GRC platform through a standardized interface.

## Overview

This project provides a local server that implements the Model Context Protocol (MCP) to interact with IBM OpenPages. It allows AI agents to perform operations on OpenPages objects like issues and controls through a standardized interface. For more information on MCP, visit [the official documentation](https://modelcontextprotocol.io/docs/getting-started/intro).

### Architecture

<img width="1172" alt="image" src="https://github.ibm.com/OpenPages/grc-mcp-server-beta/assets/482626/7bd172b0-282d-4792-bc81-ef971c11bc95">

The OpenPages MCP Server is designed to run locally alongside AI agents and communicates with them via Standard Input/Output (STDIO). This architecture offers several advantages:

1. **Local Execution**: The server runs on the same machine as the agent, eliminating the need for remote server deployment and reducing latency.

2. **STDIO Communication**: The server uses STDIO for communication with agents, which is a simple, reliable, and language-agnostic protocol. This allows the server to be easily integrated with various AI agents regardless of their implementation language.

3. **JSON-RPC Protocol**: The server implements the JSON-RPC protocol over STDIO, enabling structured communication between the agent and the server. The agent sends JSON-RPC requests to the server, which processes them and returns JSON-RPC responses.

4. **Secure Connection to OpenPages**: While the server communicates with agents locally via STDIO, it establishes secure connections to the OpenPages instance using authentication credentials (API key or username/password).

5. **Tool-based Interface**: The server exposes a set of tools that agents can use to interact with OpenPages, abstracting away the complexity of the OpenPages API and providing a consistent interface.

6. **Platform Compatibility**: Some AI platforms, including IBM watsonx.orchestrate, specifically support local MCP servers rather than remote ones. This local architecture ensures compatibility with these platforms, making it the preferred approach for integrating OpenPages with enterprise AI systems.

This architecture makes the OpenPages MCP Server ideal for integration with various AI agents, including watsonx assistant, Claude Desktop, and other MCP-compatible agents.

## Features

- **Dynamic Object Type Support**: Extensible architecture that supports multiple OpenPages object types (Issues, Controls, Risks, and more) through a configuration-driven approach
- **CRUD Operations**: Create, update, query, and delete operations for all configured object types
- **Dynamic Schema Generation**: Automatic schema generation based on OpenPages object type definitions
- **Flexible Authentication**: Support for both basic and bearer authentication methods
- **Development-Friendly**: Configurable SSL verification for development environments
- **Configuration-Based**: Easy addition of new object types through JSON configuration without code changes

## Dynamic Object Type Architecture

The OpenPages MCP Server uses a dynamic, configuration-driven approach to support multiple OpenPages object types. This architecture allows you to easily extend the server to support new object types without modifying the core code.

### Configuration File: `object_types.json`

The server uses a JSON configuration file to define the object types it supports. Each object type configuration includes:

```json
{
  "object_types": [
    {
      "type_id": "SOXControl",           // OpenPages object type ID
      "tool_prefix": "control",          // Prefix for tool names (e.g., create_control)
      "display_name": "Control",         // Human-readable name
      "path_prefix": "Controls",         // API path prefix
      "status_field": "OPSS-Ctl:Status"  // Status field identifier
    },
    {
      "type_id": "SOXIssue",
      "tool_prefix": "issue",
      "display_name": "Issue",
      "path_prefix": "Issue",
      "status_field": "OPSS-Iss:Status"
    },
    {
      "type_id": "SOXRisk",
      "tool_prefix": "risk",
      "display_name": "Risk",
      "path_prefix": "Risk",
      "status_field": "OPSS-Risk:Status"
    }
  ]
}
```

### How It Works

1. **Automatic Tool Generation**: The server reads `object_types.json` at startup and automatically generates MCP tools for each configured object type
2. **Schema Discovery**: For each object type, the server queries OpenPages to retrieve the field schema and generates appropriate tool parameters
3. **Consistent Interface**: All object types follow the same CRUD pattern (create, update, query, delete), ensuring a consistent interface
4. **Easy Extension**: To add support for a new object type, simply add a new entry to `object_types.json` with the appropriate configuration

### Adding New Object Types

To add support for a new OpenPages object type:

1. Add a new entry to `object_types.json` with the object type details
2. Restart the MCP server
3. The server will automatically generate the necessary tools for the new object type

Example for adding a new "Action" object type:
```json
{
  "type_id": "SOXAction",
  "tool_prefix": "action",
  "display_name": "Action",
  "path_prefix": "Actions",
  "status_field": "OPSS-Act:Status"
}
```

## Prerequisites

- Python 3.11+
- Access to an IBM OpenPages instance
- Authentication credentials (username/password or API key)

## Installation

1. Clone this repository:
   ```
   git clone https://github.ibm.com/OpenPages/grc-mcp-server-beta
   cd grc-mcp-server-beta
   ```

2. Create and activate a Python virtual environment (recommended best practice):
   
   **On macOS/Linux:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
   
   **On Windows:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```
   cp .env.example .env
   ```
   Edit the `.env` file with your OpenPages connection details.

## Configuration

The following environment variables can be configured in the `.env` file:

### OpenPages Configuration
- `OPENPAGES_BASE_URL`: URL of your OpenPages instance
- `OPENPAGES_AUTHENTICATION_TYPE`: Authentication type (`basic` or `bearer`)
  - Use `basic` for on-premises installations
  - Use `bearer` for SaaS IBM Cloud hybrid deployments
- `OPENPAGES_USERNAME`: Username for basic authentication
- `OPENPAGES_PASSWORD`: Password for basic authentication
- `OPENPAGES_APIKEY`: API key for bearer authentication
- `OPENPAGES_AUTHENTICATION_URL`: Authentication URL for bearer authentication

### Server Configuration
- `DEBUG`: Enable debug mode (`True` or `False`)
- `SSL_VERIFY`: Enable SSL verification (`True` or `False`)
  - Set to `True` for SaaS deployments (recommended for production)
  - Set to `False` for on-premises local Fyre-based Docker installations
- `LOG_LEVEL`: Logging level (`INFO`, `DEBUG`, `WARNING`, `ERROR`)
- `PORT`: Server port (default: 8000)
- `HOST`: Server host (default: 0.0.0.0)

## Usage

### Starting the MCP Server

1) Start the MCP server by CLI:

```
python start_mcp.py
```

For debug mode:

```
python start_mcp.py --debug
```

### Local Testing Options

You can test the MCP server locally using one of the following methods:

#### 1. Using Python CLI with JSON-RPC Requests

You can send JSON-RPC requests directly to the server and receive responses:

1. Start the MCP server:
   ```bash
   python start_mcp.py
   ```

2. In the same terminal, send JSON-RPC requests. For example, to list available tools:
   ```json
   {"method":"tools/list","params":{"_meta":{"progressToken":1}},"jsonrpc":"2.0","id":1}
   ```

3. Press Enter to send the request. The server will respond with the tools definitions.

4. You can test other JSON-RPC methods such as:
   - List tools: `{"method":"tools/list","params":{"_meta":{"progressToken":1}},"jsonrpc":"2.0","id":1}`
   - Call a tool: `{"method":"tools/call","params":{"name":"tool_name","arguments":{}},"jsonrpc":"2.0","id":2}`

#### 2. Using MCP Inspector UI

For a more user-friendly testing experience, you can use the MCP Inspector UI (requires Node.js):

1. Run the following command from the base folder of the MCP Server:
   ```
   npx @modelcontextprotocol/inspector@latest
   ```

2. The MCP Inspector UI will open in your browser. Configure it with the following settings:
   - **Transport Type**: STDIO
   - **Command**: Python
   - **Arguments**: start_mcp.py

3. Click on "Connect", and the MCP Inspector will start the MCP server and connect to it via STDIO.
   
   <img width="1496" alt="image" src="https://github.ibm.com/OpenPages/grc-mcp-server-beta/assets/482626/caf3e170-a7b7-4401-b64a-2d1290faf0c4">


4. Go to the "Tools" tab and click on "List Tools" to see all available tools.
   
   <img width="1418" alt="image" src="https://github.ibm.com/OpenPages/grc-mcp-server-beta/assets/482626/2a8b50c1-3ef6-4e5e-9127-f5bdb157b3a2">


5. Click on any tool, fill in the required fields, and click on "Run Tool" to test the tool
   
   <img width="1503" alt="image" src="https://github.ibm.com/OpenPages/grc-mcp-server-beta/assets/482626/78cea5dc-6357-4bab-a586-c8a2d60417ba">

6. The tool runs and result is fetched
   
   <img width="1505" alt="image" src="https://github.ibm.com/OpenPages/grc-mcp-server-beta/assets/482626/129a0ea4-8db5-41ed-b51a-44e6e87ad441">



## Available Tools

The server dynamically generates MCP tools based on the object types configured in `object_types.json`. For each configured object type, the following tools are automatically created:

### Standard CRUD Operations (per Object Type)

For each object type (e.g., Issue, Control, Risk), the following tools are generated:

- **`create_{object_type}`**: Create a new object in OpenPages
  - Example: `create_issue`, `create_control`, `create_risk`
  
- **`update_{object_type}`**: Update an existing object
  - Example: `update_issue`, `update_control`, `update_risk`
  
- **`query_{object_type}s`**: Search for objects with filtering options
  - Example: `query_issues`, `query_controls`, `query_risks`
  
- **`delete_{object_type}`**: Delete an object by ID
  - Example: `delete_issue`, `delete_control`, `delete_risk`

### Currently Configured Object Types

Based on the default `object_types.json` configuration, the following tools are available:

#### Issue Management
- `create_issue`: Create a new issue in OpenPages
- `update_issue`: Update an existing issue
- `query_issues`: Search for issues with filtering options
- `delete_issue`: Delete an issue by resource ID

#### Control Management
- `create_control`: Create a new control in OpenPages
- `update_control`: Update an existing control
- `query_controls`: Search for controls with filtering options
- `delete_control`: Delete a control by resource ID

#### Risk Management
- `create_risk`: Create a new risk in OpenPages
- `update_risk`: Update an existing risk
- `query_risks`: Search for risks with filtering options
- `delete_risk`: Delete a risk by resource ID

### Utility
- `echo`: Simple echo tool for testing connectivity

## Integration with IBM watsonX orchestrate

### Prerequisites
1. OpenPages SaaS instance and an APIKey with OpenPages access
2. IBM watsonX orchestrate instance and an APIKey with watsonx orchestrate access
3. A running local environment of watsonx Agent Development Kit (ADK) - Check out the [getting started with ADK tutorial](https://developer.ibm.com/tutorials/getting-started-with-watsonx-orchestrate/) if you don't have an active instance
4. Read Access to OpenPages MCP Server repo - https://github.ibm.com/OpenPages/grc-mcp-server-beta

### Steps to Import MCP Tools to watsonX orchestrate

1. Checkout the OpenPages MCP Server code to your local machine:
   ```
   git clone https://github.ibm.com/OpenPages/grc-mcp-server-beta
   cd grc-mcp-server-beta
   ```

2. Create a `.env` file in the base folder by copying the content from `.env.example`:
   ```
   cp .env.example .env
   ```

3. Add the following configuration values in the `.env` file:
   ```
   # OpenPages Configuration
   OPENPAGES_BASE_URL=<Valid OpenPages SaaS URL>
   OPENPAGES_APIKEY=<APIKey with access to openpages instance>
   OPENPAGES_AUTHENTICATION_URL=<Auth URL of the OpenPages instance, e.g., https://iam.test.cloud.ibm.com/identity/token for IBM cloud test>
   OPENPAGES_AUTHENTICATION_TYPE=bearer
   # Keep other configs as-is
   ```

4. Load the MCP tools into your watsonx orchestrate instance using the following command (replace placeholders with your values):
   ```
   orchestrate toolkits add \
     --kind mcp \
     --name "YourOpenPagesToolsName" \
     --description "MCP tools for OpenPages integration" \
     --package-root "Base Folder of the OpenPages MCP Server code" \
     --command '["python3", "start_mcp.py"]' \
     --tools "*"
   ```

5. Enter the APIKey when prompted, and the tools will be loaded to the watsonx orchestrate instance. 
   ```
   Note: Sometimes watsonx tools import will give error like "requests.exceptions.HTTPError:
   500 Server Error: Internal Server Error".In such cases, retry with a new toolName).

   If still retry fails, then remove the contents of requirements.txt and save it and again perform
   the tool import with a new name.
   ```

### Creating an Agent with OpenPages MCP Tools

1. In the watsonx Orchestrate "Agent Builder" screen, create a new Agent.

2. Fill in the name and description:
   - **Name**: IBM OpenPages Agent (or any name you prefer)
   - **Description**: An intelligent OpenPages agent equipped with tools to perform CRUD operations on key GRC entities such as Issues, Controls, Risks, and Actions. It can create, retrieve, update, and delete records efficiently while ensuring data integrity and adherence to OpenPages data models and business rules.

3. Go to the Toolset section, click "Add tool" to add the MCP tools imported in the previous steps. Add all 6 OpenPages tools.

4. Go to the Behavior section and define how the agent should react to requests with the following instructions:

   ```
   For OpenPages operations:
   - Use openpages-mcp-tools:create_issue, update_issue, query_issues for issue management
   - Use openpages-mcp-tools:create_control, update_control, query_controls for control management
   - Format user input according to tool schema requirements
   
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
   
   Technical considerations:
   - Start MCP server only once per session
   - Provide detailed error information for debugging when tools fail
   ```

5. Deploy the Agent.

### Testing the Agent

You can test the agent either from the Preview right pane or by selecting the agent in the watsonx Orchestrate home page and chatting with it. Here are some sample prompts to test different OpenPages Tools:

#### Issue Management Examples

##### 1. Create Issue (create_issue tool)
```
Create an issue in OpenPages with the following details
Name - Issue for business Entity ABC Ltd
Description - Mitigating infra risks
Primary parent id - 7599
Issue Owner - jayasankar.sreedharan@ibm.com
Priority - Medium
Issue Status - Open
Issue Type - Design Effectiveness
```

##### 2. Update Issue (update_issue tool)
```
Update the issue with Resource ID - 14008 and name - Issue for business Entity ABC Ltd, with the following updated properties
Description - Mitigating financial issues
Priority - High
Issue Type - Control Activity Missing
```

##### 3. Query Issue (query_issues tool)
```
Get the issue in openpages with name - 'Issue for business Entity ABC Ltd' and show the below properties
Name
Description
Primary parent id
Issue Owner
Priority
Issue Status
Issue Type
```

##### 4. Delete Issue (delete_issue tool)
```
Delete the issue with id 14008
```

#### Control Management Examples

##### 5. Create Control (create_control tool)
```
Create a control in OpenPages with the following details
Name - Control for business Entity ABC Ltd
Description - Mitigating infra risks
Control Owner -
Design Effectiveness - Not Determined
Operating Effectiveness - Effective
Control Type - Detective
Frequency - Daily
Primary parent id - 8182
```

##### 6. Update Control (update_control tool)
```
Update the control with Resource ID - 14011 and name - 'Control for business Entity ABC Ltd', with the following updated properties
Control Owner - Jayasankar.Sreedharan@ibm.com
```

##### 7. Query Control (query_controls tool)
```
Get the control in openpages with name - 'Control for business Entity ABC Ltd' and show the below properties
Name
Description
Control Owner
Design Effectiveness
Operating Effectiveness
Control Type
Frequency
Primary parent id
```

##### 8. Delete Control (delete_control tool)
```
Delete the control with id 14011
```

#### Risk Management Examples

##### 9. Create Risk (create_risk tool)
```
Create a risk in OpenPages with the following details
Name - Risk for business Entity ABC Ltd
Description - Mitigating openpages risks
Status - Awaiting Assessment
Owner - Jayasankar.Sreedharan@ibm.com
Assessment Method - Qualitative
Basel Risk Category - External Fraud
Primary parent id - 5492
Domain - Technology
```

##### 10. Update Risk (update_risk tool)
```
Update the risk with Resource ID - 14045 and name - 'Risk for business Entity ABC Ltd', with the following updated properties
Description - Mitigating financial risks
```

##### 11. Query Risk (query_risks tool)
```
Get the risk in openpages with name - 'Risk for business Entity ABC Ltd' and show the below properties
Name
Description
Status
Owner
Assessment Method
Basel Risk Category
Primary parent id
```

##### 12. Delete Risk (delete_risk tool)
```
Delete the risk with id 14045
```

### OpenPages Local MCP - WatsonX Orchestrate High Level Architecture - User Flow

<img width="1188" alt="image" src="https://github.ibm.com/OpenPages/grc-mcp-server-beta/assets/482626/57d57f3a-80a7-4ddf-9ba4-f053adc1ad6c">



## Security Considerations

- Store credentials securely and never commit them to version control
- Enable SSL verification in production environments
- Use bearer authentication with API keys when possible
- Restrict access to the server to trusted networks

## Troubleshooting

- Check the logs for detailed error messages
- Verify your OpenPages connection details
- Ensure your authentication credentials are correct
- For SSL certificate issues in development, you can set `SSL_VERIFY=False` (not recommended for production)

## OpenPages MCP Server Roadmap

The OpenPages MCP Server is continuously evolving to provide enhanced capabilities for AI integration with IBM OpenPages. Below is the roadmap outlining planned future developments:

### Current Beta Version
The current beta version of the OpenPages MCP Server is implemented as a local server with:
- CRUD operations for key entities (Issues and Controls)
- Local execution model with STDIO communication
- Integration with watsonx.orchestrate and other MCP-compatible agents

### Short-term Enhancements
- **Enhanced Query Capabilities**: Improve filtering, sorting, and relationship traversal in query tools
- **Use-Case Level Tools**: Develop higher-level tools that encapsulate common business processes and workflows

### Long-term Vision
- **Remote MCP Server**: Develop support for remote MCP server deployment that can be independently scaled alongside OpenPages instances
- **HTTP Streaming Communication**: Implement streamable HTTP communication with agents for improved performance and scalability
- **Advanced Analytics Integration**: Tools for integrating OpenPages data with analytics and reporting capabilities

This roadmap represents our commitment to making OpenPages data and functionality more accessible to AI agents while maintaining security, performance, and usability.

## License

[Specify license information]

