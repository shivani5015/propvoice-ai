from mcp_server.tools import mcp

if __name__ == "__main__":
    print("Ready. Server chalu: http://127.0.0.1:8001/mcp")
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8001)
