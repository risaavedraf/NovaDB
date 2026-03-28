"""
NovaDB MCP Tools - Contexto

Tools for context, updates, and connections.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import logging
from typing import Optional, Dict, Any

from novadb import NovaDB
from ..serializers import serialize_node
from ..config import get_config

logger = logging.getLogger(__name__)


def get_db() -> "NovaDB":
    """Get NovaDB instance from memoria module."""
    from .memoria import get_db as _get_db
    return _get_db()


def reflejar(
    node_id: str,
    profundidad: int = 1
) -> Dict[str, Any]:
    """
    Obtiene el contexto alrededor de un nodo (padres, hijos, vecinos).
    
    Args:
        node_id: El ID del nodo central
        profundidad: Qué tan profundo explorar (1-3, default: 1)
    
    Returns:
        Nodo central + su vecindario
    """
    try:
        db = get_db()
        context = db.get_context(node_id, depth=profundidad)
        return {
            "success": True,
            "context": context
        }
    except Exception as e:
        logger.error("Error reflecting: %s", e)
        return {"success": False, "error": str(e)}


def actualizar(
    node_id: str,
    texto: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Actualiza un recuerdo existente.
    
    Args:
        node_id: El ID del nodo a actualizar
        texto: Nuevo texto (opcional)
        metadata: Metadata a mergear (opcional)
    
    Returns:
        Confirmación de actualización
    """
    try:
        db = get_db()
        fields = {}
        if texto is not None:
            fields["text"] = texto
        if metadata is not None:
            fields["metadata"] = metadata
        
        if not fields:
            return {"success": False, "error": "No se especificaron campos para actualizar"}
        
        db.update(node_id=node_id, fields=fields)
        db.save(get_config().db_path)
        return {
            "success": True,
            "message": f"✅ Nodo {node_id} actualizado"
        }
    except Exception as e:
        logger.error("Error updating: %s", e)
        return {"success": False, "error": str(e)}


def conectar(
    origen_id: str,
    destino_id: str,
    tipo_conexion: str = "cruzada",
    peso: float = 1.0
) -> Dict[str, Any]:
    """
    Crea una conexión explícita entre dos memorias.
    
    Args:
        origen_id: ID del nodo origen
        destino_id: ID del nodo destino
        tipo_conexion: Tipo de conexión (cruzada, vecino)
        peso: Peso de la conexión (0.0-1.0)
    
    Returns:
        Confirmación de conexión
    """
    try:
        db = get_db()
        db.connect(origen_id, destino_id, tipo_conexion, peso)
        db.save(get_config().db_path)
        return {
            "success": True,
            "message": f"✅ Conectados {origen_id} ↔ {destino_id}"
        }
    except Exception as e:
        logger.error("Error connecting: %s", e)
        return {"success": False, "error": str(e)}


def register(mcp):
    @mcp.tool(name="reflejar", description="Obtiene el contexto alrededor de un nodo (padres, hijos, vecinos).")
    def _reflejar(node_id: str, profundidad: int = 1) -> Dict[str, Any]:
        return reflejar(node_id, profundidad)
    
    @mcp.tool(name="actualizar", description="Actualiza un recuerdo existente en el sistema.")
    def _actualizar(
        node_id: str,
        texto: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return actualizar(node_id, texto, metadata)
    
    @mcp.tool(name="conectar", description="Crea una conexión explícita entre dos memorias.")
    def _conectar(
        origen_id: str,
        destino_id: str,
        tipo_conexion: str = "cruzada",
        peso: float = 1.0
    ) -> Dict[str, Any]:
        return conectar(origen_id, destino_id, tipo_conexion, peso)
