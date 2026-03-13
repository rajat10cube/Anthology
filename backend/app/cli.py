#!/usr/bin/env python3
"""CLI entry point for the Anthology MCP server.

Usage:
    anthology-mcp          # starts the stdio MCP server
    python -m app.cli      # alternative
"""
import asyncio
import sys

from app.mcp_server import main as _mcp_main


def main() -> None:
    """Entry point for the `anthology-mcp` console script."""
    try:
        asyncio.run(_mcp_main())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
