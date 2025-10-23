# OpenPages Local MCP Server

A local MCP (Machine Comprehension Protocol) server for IBM OpenPages that can run alongside agents like watsonx assistant, Claude Desktop, etc.

## Overview

This project provides a local server that implements the MCP protocol to interact with IBM OpenPages. It allows AI agents to perform operations on OpenPages objects like issues and controls through a standardized interface.

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

Start the MCP server:

```
python start_mcp.py
```

For debug mode:

```
python start_mcp.py --debug
```

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

## License

[Specify license information]