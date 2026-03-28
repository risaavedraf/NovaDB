"""
NovaDB MCP Tests - Server

Tests for MCP server initialization and tool registration.
"""

import pytest
from unittest.mock import patch, MagicMock

def test_server_creation():
    """Test that FastMCP server is created correctly."""
    from novadb_mcp.server import mcp
    assert mcp is not None
    assert mcp.name == "NovaDB"

def test_server_has_instructions():
    """Test that server has instructions."""
    from novadb_mcp.server import mcp
    assert mcp.instructions is not None
    assert "memoria" in mcp.instructions.lower()

def test_all_tools_exported():
    """Test that all tool functions are exported from modules."""
    from novadb_mcp.tools import memoria, contexto, sistema, admin
    from novadb_mcp.tools.memoria import memorizar, recordar, obtener, olvidar
    from novadb_mcp.tools.contexto import reflejar, actualizar, conectar
    from novadb_mcp.tools.sistema import analizar, rebalancear
    from novadb_mcp.tools.admin import guardar, cargar, exportar
    
    expected_tools = {
        "memoria": ["memorizar", "recordar", "obtener", "olvidar"],
        "contexto": ["reflejar", "actualizar", "conectar"],
        "sistema": ["analizar", "rebalancear"],
        "admin": ["guardar", "cargar", "exportar"],
    }
    
    for module_name, tool_names in expected_tools.items():
        module = locals()[module_name]
        for tool_name in tool_names:
            assert hasattr(module, tool_name), f"Tool {tool_name} not found in {module_name}"
