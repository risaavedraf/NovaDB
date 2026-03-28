"""
NovaDB MCP Tests - Fixtures

Shared test fixtures for mocking NovaDB and MCP server.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import numpy as np

@pytest.fixture
def mock_node():
    """Create a mock Node object."""
    node = MagicMock()
    node.id = "test-node-123"
    node.text = "Test memory content"
    node.tipo = "MEMORIA"
    node.metadata = {"source": "test"}
    node.padres = []
    node.hijos = []
    node.vecinos = []
    node.accesos = 0
    node.relevancia = 0.5
    node.created_at = datetime(2026, 3, 25, 12, 0, 0)
    node.updated_at = datetime(2026, 3, 25, 12, 0, 0)
    return node

@pytest.fixture
def mock_novadb(mock_node):
    """Create a mock NovaDB instance."""
    db = MagicMock()
    db.insert.return_value = "test-node-123"
    db.search.return_value = [(mock_node, 0.85)]
    db.get.return_value = mock_node
    db.get_context.return_value = {
        "node": {"id": "test-node-123", "text": "Test"},
        "padres": [],
        "hijos": [],
        "vecinos": []
    }
    db.stats.return_value = {
        "total_nodos": 100,
        "por_tipo": {"MACRO": 5, "MEDIO": 15, "MEMORIA": 80},
        "nodos_huerfanos": 3,
        "relevancia_promedio": 0.45
    }
    db.rebalancear.return_value = {"fusionados": 2, "redistribuidos": 5}
    return db

@pytest.fixture
def mock_config(tmp_path):
    """Create a mock config."""
    config = MagicMock()
    config.db_path = str(tmp_path / "test.msgpack")
    config.is_gemini_available = True
    config.k_vecinos = 5
    config.umbral_padre = 0.70
    config.umbral_vecino = 0.65
    config.access_boost = 0.15
    config.decay_rate = 0.0001
    config.relevancia_weight = 0.3
    return config

@pytest.fixture(autouse=True)
def reset_db():
    """Reset the global _db between tests."""
    from novadb_mcp.tools import memoria
    memoria._db = None
    yield
    memoria._db = None
