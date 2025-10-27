# OpenPages Local MCP Server

A local Machine Comprehension Protocol (MCP) server that enables AI agents to securely interact with IBM OpenPages GRC platform through a standardized interface.

## Overview

This project provides a local server that implements the Machine Comprehension Protocol (MCP) to interact with IBM OpenPages. It allows AI agents to perform operations on OpenPages objects like issues and controls through a standardized interface.

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

- Create, update, and query issues in OpenPages
- Create, update, and query controls in OpenPages
- Dynamic schema generation based on OpenPages object types
- Support for both basic and bearer authentication
- Configurable SSL verification for development environments

## Prerequisites

- Python 3.8+
- Access to an IBM OpenPages instance
- Authentication credentials (username/password or API key)

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd openpages-mcp-server
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```
   cp .env.example .env
   ```
   Edit the `.env` file with your OpenPages connection details.

## Configuration

The following environment variables can be configured in the `.env` file:

### OpenPages Configuration
- `OPENPAGES_BASE_URL`: URL of your OpenPages instance
- `OPENPAGES_AUTHENTICATION_TYPE`: Authentication type (`basic` or `bearer`)
- `OPENPAGES_USERNAME`: Username for basic authentication
- `OPENPAGES_PASSWORD`: Password for basic authentication
- `OPENPAGES_APIKEY`: API key for bearer authentication
- `OPENPAGES_AUTHENTICATION_URL`: Authentication URL for bearer authentication

### Server Configuration
- `DEBUG`: Enable debug mode (`True` or `False`)
- `SSL_VERIFY`: Enable SSL verification (`True` or `False`)
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

Example: List tools JSON-RPC request
```
{"method":"tools/list","params":{"_meta":{"progressToken":1}},"jsonrpc":"2.0","id":1}
```

The response will contain the tools definitions.

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


5. Go to the "Tools" tab and click on "List Tools" to see all available tools.
   
   <img width="1418" alt="image" src="https://github.ibm.com/OpenPages/grc-mcp-server-beta/assets/482626/2a8b50c1-3ef6-4e5e-9127-f5bdb157b3a2">


7. Click on any tool, fill in the required fields, and click on "Run Tool" to test the tool
   
   <img width="1503" alt="image" src="https://github.ibm.com/OpenPages/grc-mcp-server-beta/assets/482626/78cea5dc-6357-4bab-a586-c8a2d60417ba">

8. The tool runs and result is fetched
   
   <img width="1505" alt="image" src="https://github.ibm.com/OpenPages/grc-mcp-server-beta/assets/482626/129a0ea4-8db5-41ed-b51a-44e6e87ad441">



## Available Tools

The server provides the following MCP tools:

### Issue Management
- `create_issue`: Create a new issue in OpenPages
- `update_issue`: Update an existing issue
- `query_issues`: Search for issues with filtering options

### Control Management
- `create_control`: Create a new control in OpenPages
- `update_control`: Update an existing control
- `query_controls`: Search for controls with filtering options

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
   orchestrate toolkits import \
     --kind mcp \
     --name "YourOpenPagesToolsName" \
     --description "MCP tools for OpenPages integration" \
     --package-root "Base Folder of the OpenPages MCP Server code" \
     --command '["python3", "start_mcp.py"]' \
     --tools "*"
   ```

5. Enter the APIKey when prompted, and the tools will be loaded to the watsonx orchestrate instance. (Note: Someone watsonx tools import will give error like "requests.exceptions.HTTPError: 500 Server Error: Internal Server Error". In such cases, retry with a new toolName)

### Creating an Agent with OpenPages MCP Tools

1. In the watsonx Orchestrate "Agent Builder" screen, create a new Agent.

2. Fill in the name and description:
   - **Name**: IBM OpenPages Agent (or any name you prefer)
   - **Description**: An intelligent OpenPages agent equipped with tools to perform CRUD operations on key GRC entities such as Issues, Controls, Risks, and Actions. It can create, retrieve, update, and delete records efficiently while ensuring data integrity and adherence to OpenPages data models and business rules.

3. Go to the Toolset section, click "Add tool" to add the MCP tools imported in the previous steps. Add all 6 OpenPages tools.

4. Go to the Behavior section and define how the agent should react to requests with the following instructions:
   ```
   For reasoning or English-language tasks, depend on the LLM's own capabilities to provide answers directly. For openpages Issue/Control creation, such as creating a new Issue(or new Control), call the MCP tools to create the issue (or control) entity in Openpages and return back the created issue (control) details.
   - Use tool openpages-mcp-tools:create_issue to create issue taking the user arguments and showing the created issue details
   - Use tool openpages-mcp-tools:update_issue to update issue taking the user arguments and showing the upated issue details
   - Use tool openpages-mcp-tools:query_issues to fetch issues based on any filter conditions
   - Use tool openpages-mcp-tools:create_control to create issue taking the user arguments and showing the created issue details
   - Use tool openpages-mcp-tools:update_control to update issue taking the user arguments and showing the upated issue details
   - Use tool openpages-mcp-tools:query_controls to fetch issues based on any filter conditions

   Convert the user supplied input into the proper json format as defined in the tool specific schema.
   Start the mcp server and tools only once and use it for all the conversation and don't start the mcp server for each conversation as it will slow down the user's chat experience.

   If the mcp tools integration is erroring, give a clear error message to a technical user on why and how its failing in depth for easy debugging and fixing.
   ```

5. Deploy the Agent.

### Testing the Agent

You can test the agent either from the Preview right pane or by selecting the agent in the watsonx Orchestrate home page and chatting with it. Here are some sample prompts to test different OpenPages Tools:

#### 1. Create Issue (create_issue tool)
```
Create an issue in OpenPages with the following details
Name - Issue for business ABCD Corp LTD
Description - Mitigting infra risks
Primary parent id - 7599
OPSS-Iss:Assignee - jayasankar.sreedharan@ibm.com
OPSS-Iss:Priority - Medium
OPSS-Iss:Status - Open
OPSS-Iss:Issue Type - Design Effectiveness
```

#### 2. Update Issue (update_issue tool)
```
Update the issue with Resource ID - 11004 and name - Issue for business ABCD Corp LTD, with the following updated properties
Description - Mitigating infra issues
OPSS-Iss:Priority - High
OPSS-Iss:Issue Type - Control Activity Missing
```

#### 3. Query Issue (query_issue tool)
```
Get the issue in openpages with name - Issue for business ABCD Corp LTD and show the properties in bullet points
```

#### 4. Create Control (create_control tool)
```
Create a control in OpenPages with the following details
Name - Control for business ABCD Corp LTD
Description - Mitigting infra risks
OPSS-Ctl:Control Owner - jayasankar.sreedharan@ibm.com
OPSS-Ctl:Design Effectiveness - Not Determined
OPSS-Ctl:Operating Effectiveness - Effective
OPSS-Ctl:Control Type - Detective
OPSS-Ctl:Frequency - Daily
Primary parent id - 8182
```

#### 5. Update Control (update_control tool)
```
Update the control with Resource ID - 11006 and name - Control for business ABCD Corp LTD, with the following updated properties
Description - Mitigating infra issues
OPSS-Ctl:Frequency - Weekly
OPSS-Ctl:Control Type - Administrative
```

#### 6. Query Control (query_control tool)
```
Get the Control in openpages with name - Control for business ABCD Corp LTD, and show all the available properties in bullet points
```

### OpenPages Local MCP - WatsxonX Orchestrate High Level Architecture - user flow

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
- **Expanded Entity Support**: Add CRUD operations for additional OpenPages entities such as Risks, Actions, and Assessments
- **Enhanced Query Capabilities**: Improve filtering, sorting, and relationship traversal in query tools
- **Use-Case Level Tools**: Develop higher-level tools that encapsulate common business processes and workflows

### Long-term Vision
- **Remote MCP Server**: Develop support for remote MCP server deployment that can be independently scaled alongside OpenPages instances
- **HTTP Streaming Communication**: Implement streamable HTTP communication with agents for improved performance and scalability
- **Advanced Analytics Integration**: Tools for integrating OpenPages data with analytics and reporting capabilities

This roadmap represents our commitment to making OpenPages data and functionality more accessible to AI agents while maintaining security, performance, and usability.

## License

[Specify license information]
