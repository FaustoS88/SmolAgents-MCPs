# SmolAgents + MCP servers

This project demonstrates building an AI assistant using the SmolAgents library that can perform web searches and scrape/crawl websites by integrating with the Brave Search and the Crawl4ai Model Context Protocols (MCP) servers.

## Requirements

Before running this project, ensure you have the following dependencies installed:

- `smolagents`
- `python-dotenv`
- `mcp`
- `@modelcontextprotocol/server-brave-search` (installed globally via npm/npx)
- `litellm`

You can install the Python packages using pip:

```bash
pip install -r requirements.txt
```

Ensure you have Node.js and npm/npx and uv installed to run the MCP servers.

## Environment Variables

Create a `.env` file in the root directory of the project and add the following variables:

```
BRAVE_API_KEY=your_brave_api_key
OPENAI_API_KEY=your_openai_api_key
```

Replace `your_brave_api_key` and `your_openai_api_key` with your actual API keys.

## Usage

1.  Clone the repository or download the script (`smolagent_with_mcp.py`).
2.  Navigate to the project directory in your terminal.
3.  Run the script:

    ```bash
    python smolagent_with_mcp.py
    ```

4.  Interact with the assistant by typing your search queries. Type `exit` or `quit` to terminate the session.

the code encapsulates the agent initialization and the main interaction loop within a Python class (`SmolAgentWithMCP`). This object-oriented approach offers modularity and makes it easier to extend the agent's capabilities, such as integrating additional MCP servers and their tools.

## Notes

*   Ensure that `npx` is installed and available in your system's PATH, as it is required to run the Brave Search MCP server.
*   The `ToolCallingAgent` in SmolAgents is designed to output tool calls in a structured format (like JSON) which are then executed by the environment (in this case, the script's main loop using the `MCPClient`).

## Adding More MCP Servers

The `smolagent_with_mcp.py` file is structured to allow for easily adding more MCP servers and their tools in a modular way. To add a new MCP server:

1.  Define the `StdioServerParameters` for the new server. This involves specifying the command to run the server, its arguments, and any necessary environment variables (similar to how `brave_server_params` and `crawl4ai_server_params` are defined).

2.  Add the newly defined server parameters object to the `server_list` in the `main` function. The `BraveSearchAgentApp` class will automatically initialize the new server and include its tools in the agent's capabilities.

Example:

```python
# Define parameters for a new server (replace with actual command and args)
new_server_params = StdioServerParameters(
    command="your_server_command",
    args=["arg1", "arg2"],
    env={"YOUR_API_KEY": os.getenv("YOUR_API_KEY")},
)

def main():
    # Define the list of MCP server parameters
    server_list = [
        brave_server_params,
        crawl4ai_server_params,
        new_server_params # Add the new server parameters here
        # Add other server parameters here as needed
    ]
    app = BraveSearchAgentApp(server_list)
    app.run()

if __name__ == "__main__":
    main()
```

## MCP used in the project:
https://playbooks.com/mcp/ritvij14-crawl4ai
https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search


## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
