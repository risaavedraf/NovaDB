"""
NovaDB MCP Server

Main server definition using FastMCP.
Exposes NovaDB's memory engine as MCP tools for AI agents.

IMPORTANT: MCP uses stdio for communication. ALL logging MUST go to file,
never to stdout/stderr, or the protocol stream gets corrupted.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import logging
import os
import tempfile

# CRITICAL: Configure logging to FILE before ANY imports
# This prevents ANY output to stdout/stderr that would corrupt MCP stream
log_file = os.environ.get("NOVADB_LOG_FILE", 
    os.path.join(tempfile.gettempdir(), "novadb-mcp.log"))

# Remove ALL existing handlers from root logger
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Configure ONLY file handler
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
))
logging.root.addHandler(file_handler)
logging.root.setLevel(logging.INFO)

# Silence ALL loggers that might write to stdout/stderr
for name in ['novadb', 'novadb_mcp', 'httpx', 'google', 'urllib3', 
             'novadb.core', 'novadb.core.logging_config']:
    logging.getLogger(name).setLevel(logging.CRITICAL)
    logging.getLogger(name).propagate = False

# Our MCP logger uses file only
logger = logging.getLogger('novadb_mcp')
logger.setLevel(logging.INFO)

from .config import get_config
from mcp.server.fastmcp import FastMCP
from .tools import memoria, contexto, sistema, admin

mcp = FastMCP(
    "NovaDB",
    instructions="""
NovaDB es tu motor de memoria semántica jerárquica.
Usa las herramientas disponibles para guardar, buscar y organizar recuerdos.
Cada recuerdo se almacena como un nodo con embedding semántico.
"""
)

memoria.register(mcp)
contexto.register(mcp)
sistema.register(mcp)
admin.register(mcp)

def main():
    """Entry point for the MCP server."""
    # Los logs ya están configurados al inicio del archivo a file
    mcp.run()

if __name__ == "__main__":
    main()
