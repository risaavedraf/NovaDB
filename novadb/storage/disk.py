import json
import os
import logging
import msgpack
from datetime import datetime
from novadb.core.graph import NovaGraph
from novadb.core.node import Node

logger = logging.getLogger(__name__)


def save_to_json(graph: NovaGraph, path: str, embedding_dims: int = None) -> None:
    """
    Persiste el grafo completo en disco en formato legible (JSON).
    Incluye embedding_dims para validar compatibilidad al recargar.
    Uses atomic write (temp file + rename) to prevent corruption on crash.
    """
    data = {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "k_vecinos": graph.k_vecinos,
        "embedding_dims": embedding_dims,
        "nodes": {
            node_id: node.to_dict() for node_id, node in graph.nodes.items()
        }
    }

    directorio = os.path.dirname(os.path.abspath(path))
    if directorio:
        os.makedirs(directorio, exist_ok=True)

    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, path)  # Atomic on same filesystem
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def load_from_json(path: str) -> tuple:
    """
    Carga un grafo completo desde un archivo JSON.
    Returns: (NovaGraph, embedding_dims or None)
    """
    if not os.path.exists(path):
        logger.error("Database file not found: %s", path)
        raise FileNotFoundError(f"Database file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    k_vecinos: int = data.get("k_vecinos", 5)
    embedding_dims = data.get("embedding_dims", None)
    graph: NovaGraph = NovaGraph(k_vecinos=k_vecinos)

    for _, node_data in data.get("nodes", {}).items():
        node = Node.from_dict(node_data)
        graph.nodes[node.id] = node

    graph.rebuild_indices()
    return graph, embedding_dims


def save_to_msgpack(graph: NovaGraph, path: str, embedding_dims: int = None) -> None:
    """
    Persiste el grafo en disco en formato binario (MessagePack).
    3-5x más compacto y rápido que JSON para producción.
    Incluye embedding_dims para validar compatibilidad al recargar.
    Uses atomic write (temp file + rename) to prevent corruption on crash.
    """
    data = {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "k_vecinos": graph.k_vecinos,
        "embedding_dims": embedding_dims,
        "nodes": {
            node_id: node.to_dict() for node_id, node in graph.nodes.items()
        }
    }

    directorio = os.path.dirname(os.path.abspath(path))
    if directorio:
        os.makedirs(directorio, exist_ok=True)

    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "wb") as f:
            packed = msgpack.packb(data, use_bin_type=True)
            f.write(packed)
        os.replace(tmp_path, path)  # Atomic on same filesystem
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def load_from_msgpack(path: str) -> tuple:
    """
    Carga un grafo desde un archivo MessagePack.
    Returns: (NovaGraph, embedding_dims or None)
    """
    if not os.path.exists(path):
        logger.error("Database file not found: %s", path)
        raise FileNotFoundError(f"Database file not found: {path}")

    with open(path, "rb") as f:
        data = msgpack.unpackb(f.read(), raw=False)

    k_vecinos: int = data.get("k_vecinos", 5)
    embedding_dims = data.get("embedding_dims", None)
    graph: NovaGraph = NovaGraph(k_vecinos=k_vecinos)

    for _, node_data in data.get("nodes", {}).items():
        node: Node = Node.from_dict(node_data)
        graph.nodes[node.id] = node

    graph.rebuild_indices()
    return graph, embedding_dims
