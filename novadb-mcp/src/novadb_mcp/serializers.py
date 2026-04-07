"""
NovaDB MCP Server - Serializers

Converts NovaDB objects (Node, numpy arrays) to JSON-serializable formats.
"""

import numpy as np
from typing import Any, Dict, List, Optional

def serialize_node(node) -> Dict[str, Any]:
    """Convert a Node to JSON-serializable dict."""
    if node is None:
        return None
    
    return {
        "id": node.id,
        "text": node.text,
        "tipo": node.tipo,
        "metadata": node.metadata,
        "padres": node.padres,
        "hijos": node.hijos,
        "vecinos": node.vecinos,
        "accesos": node.accesos,
        "relevancia": round(node.relevancia, 4),
        "created_at": node.created_at.isoformat() if node.created_at else None,
        "updated_at": node.updated_at.isoformat() if node.updated_at else None,
    }

def serialize_search_results(results: List[tuple]) -> List[Dict[str, Any]]:
    """Convert search results [(Node, score), ...] to JSON list."""
    return [
        {
            "node": serialize_node(node),
            "score": round(score, 4)
        }
        for node, score in results
    ]

def serialize_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure stats dict is JSON-serializable."""
    serialized = {}
    for key, value in stats.items():
        if isinstance(value, (np.integer, np.floating, np.bool_)):
            serialized[key] = value.item()
        elif isinstance(value, np.ndarray):
            serialized[key] = value.tolist()
        elif isinstance(value, dict):
            serialized[key] = serialize_stats(value)
        else:
            serialized[key] = value
    return serialized
