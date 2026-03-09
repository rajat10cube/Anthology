#!/usr/bin/env python3
"""
Entry point for the Anthology MCP Server.
Usage: python run_mcp.py
"""
import asyncio
import sys
from pathlib import Path

# Add the 'backend' dir (one level up from where we are right now) to the path
# so that imports like 'app.services.storage' resolve correctly.
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.mcp_server import main

if __name__ == "__main__":
    asyncio.run(main())
