I got this from pycharm settings: copy SSE settings

```json
{
  "type": "sse",
  "url": "http://localhost:64342/sse",
  "headers": {
    "IJ_MCP_SERVER_PROJECT_PATH": null
  }
}
```

#  in project root  !!! .mcp.json !!! 

```json
{
  "mcpServers": {
    "pycharm": {
      "type": "sse",
      "url": "http://localhost:64342/sse"
    }
  }
}
```

doesnt work !!!

# tried 

claude mcp add --transport sse pycharm "http://localhost:64342/sse" --scope user      

it add ito to ~\.claude.json outside any projects in the json root
```json
"mcpServers": {
    "pycharm": {
      "type": "sse",
      "url": "http://localhost:64342/sse"
    }
  }
```

now mcp list shows it

pycharm: http://localhost:64342/sse (SSE) - ✓ Connected

