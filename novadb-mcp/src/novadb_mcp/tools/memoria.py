"""
NovaDB MCP Tools - Memoria

Tools for storing and retrieving memories.
"""

import sys
import os
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import logging
from typing import Optional, Dict, Any, List

from novadb import NovaDB
from ..config import get_config
from ..serializers import serialize_node, serialize_search_results

logger = logging.getLogger(__name__)

_db: Optional[NovaDB] = None

def get_db() -> NovaDB:
    """Get or create NovaDB instance."""
    global _db
    if _db is None:
        import tempfile
        config = get_config()
        
        # CRITICAL: Disable all NovaDB logging to stdout/stderr
        # MCP uses stdio - ANY output corrupts the stream
        novadb_log_file = os.path.join(tempfile.gettempdir(), "novadb-engine.log")
        
        # CRITICAL: Inject API KEY into environment if not present
        if config.gemini_api_key:
            os.environ["GEMINI_API_KEY"] = config.gemini_api_key
        
        _db = NovaDB(
            k_vecinos=config.k_vecinos,
            umbral_padre=config.umbral_padre,
            umbral_vecino=config.umbral_vecino,
            access_boost=config.access_boost,
            decay_rate=config.decay_rate,
            relevancia_weight=config.relevancia_weight,
            log_level=logging.CRITICAL,
            log_file=novadb_log_file
        )
        try:
            _db.load(config.db_path)
        except FileNotFoundError:
            pass  # Fresh database - no logging needed
    return _db


def memorizar(
    texto: str,
    tipo: str = "MEMORIA",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Guarda un recuerdo en la memoria semántica.
    
    Args:
        texto: El contenido del recuerdo (obligatorio)
        tipo: Tipo de nodo - MACRO, MEDIO, o MEMORIA (default: MEMORIA)
        metadata: Datos adicionales opcionales (dict)
    
    Returns:
        Dict con el ID del nodo creado y confirmación
    """
    try:
        db = get_db()
        node_id = db.insert(text=texto, tipo=tipo, metadata=metadata)
        db.save(get_config().db_path)
        return {
            "success": True,
            "node_id": node_id,
            "message": f"✅ Memoria guardada: {texto[:50]}..."
        }
    except Exception as e:
        logger.error("Error memorizing: %s", e)
        return {"success": False, "error": str(e)}


def recordar(
    consulta: str,
    cantidad: int = 5
) -> Dict[str, Any]:
    """
    Busca recuerdos por significado semántico.
    
    Args:
        consulta: Qué buscar (se busca por significado, no por palabras exactas)
        cantidad: Cuántos resultados devolver (default: 5)
    
    Returns:
        Lista de nodos encontrados con score de similitud
    """
    try:
        db = get_db()
        results = db.search(query=consulta, n=cantidad)
        return {
            "success": True,
            "results": results, # NovaDB.search() ya retorna una lista de dicts con _score
            "total": len(results)
        }
    except Exception as e:
        logger.error("Error recalling: %s", e)
        return {"success": False, "error": str(e)}


def obtener(node_id: str) -> Dict[str, Any]:
    """
    Recupera un recuerdo específico por su ID.
    
    Args:
        node_id: El ID del nodo a recuperar
    
    Returns:
        El nodo completo con todos sus campos
    """
    try:
        db = get_db()
        node = db.get(node_id)
        if node is None:
            return {"success": False, "error": f"Nodo {node_id} no encontrado"}
        return {
            "success": True,
            "node": serialize_node(node)
        }
    except Exception as e:
        logger.error("Error getting node: %s", e)
        return {"success": False, "error": str(e)}


def olvidar(node_id: str) -> Dict[str, Any]:
    """
    Borrado quirúrgico de un nodo del grafo, sin cascada.
    Limpia todas las referencias en nodos conectados y retorna
    los IDs de nodos MEMORIA que quedaron huérfanos.

    Args:
        node_id: El ID del nodo a eliminar

    Returns:
        Dict con el ID eliminado y la lista de huérfanos
    """
    try:
        db = get_db()
        resultado = db.olvidar(node_id)
        if resultado["success"]:
            db.save(get_config().db_path)
        return resultado
    except Exception as e:
        logger.error("Error olvidando: %s", e)
        return {"success": False, "error": str(e)}


def register(mcp):
    @mcp.tool(name="memorizar", description="Guarda un recuerdo en la memoria semántica.")
    def _memorizar(
        texto: str,
        tipo: str = "MEMORIA",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return memorizar(texto, tipo, metadata)
    
    @mcp.tool(name="recordar", description="Busca recuerdos por significado semántico.")
    def _recordar(
        consulta: str,
        cantidad: int = 5
    ) -> Dict[str, Any]:
        return recordar(consulta, cantidad)
    
    @mcp.tool(name="obtener", description="Recupera un recuerdo en específico por su ID.")
    def _obtener(node_id: str) -> Dict[str, Any]:
        return obtener(node_id)
    
    @mcp.tool(name="olvidar", description="Borrado quirúrgico de un nodo del grafo, sin cascada.")
    def _olvidar(node_id: str) -> Dict[str, Any]:
        return olvidar(node_id)
