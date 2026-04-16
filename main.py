from blender_mcp.server import main as server_main
import sys

def main():
    """Entry point for the blender-mcp package.
    
    Runs the MCP server that connects Blender to AI assistants.
    """
    # Print a startup message so it's clear the server is launching
    print("Starting Blender MCP server...", file=sys.stderr)
    server_main()

if __name__ == "__main__":
    main()
