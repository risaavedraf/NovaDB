"""
NovaDB MCP Tools - Admin

Tools for persistence and export.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import logging
from typing import Optional, Dict, Any

from novadb import NovaDB
from ..config import get_config

logger = logging.getLogger(__name__)


def get_db() -> "NovaDB":
    """Get NovaDB instance from memoria module."""
    from .memoria import get_db as _get_db
    return _get_db()


def guardar(ruta: Optional[str] = None) -> Dict[str, Any]:
    """
    Persiste el grafo de memoria a disco.
    
    Args:
        ruta: Ruta personalizada (opcional, default: config.db_path)
    
    Returns:
        Confirmación de guardado
    """
    try:
        db = get_db()
        path = ruta or get_config().db_path
        db.save(path)
        return {
            "success": True,
            "path": path,
            "message": f"✅ Guardado en {path}"
        }
    except Exception as e:
        logger.error("Error saving: %s", e)
        return {"success": False, "error": str(e)}


def cargar(ruta: Optional[str] = None) -> Dict[str, Any]:
    """
    Carga un grafo de memoria desde disco.
    
    Args:
        ruta: Ruta del archivo (opcional, default: config.db_path)
    
    Returns:
        Confirmación de carga con estadísticas básicas
    """
    try:
        db = get_db()
        path = ruta or get_config().db_path
        db.load(path)
        stats = db.stats()
        return {
            "success": True,
            "path": path,
            "stats": {
                "total_nodos": stats.get("total_nodos", 0),
                "por_tipo": stats.get("por_tipo", {})
            },
            "message": f"✅ Cargado desde {path}"
        }
    except Exception as e:
        logger.error("Error loading: %s", e)
        return {"success": False, "error": str(e)}


def exportar(ruta: str) -> Dict[str, Any]:
    """
    Exporta el grafo de memoria a formato Markdown legible.
    
    Args:
        ruta: Ruta del archivo .md a generar
    
    Returns:
        Confirmación de exportación
    """
    try:
        db = get_db()
        db.export_md(ruta)
        return {
            "success": True,
            "path": ruta,
            "message": f"✅ Exportado a {ruta}"
        }
    except Exception as e:
        logger.error("Error exporting: %s", e)
        return {"success": False, "error": str(e)}


def register(mcp):
    @mcp.tool(name="guardar", description="Persiste la memoria global semántica forzando guardado a disco.")
    def _guardar(ruta: Optional[str] = None) -> Dict[str, Any]:
        return guardar(ruta)
    
    @mcp.tool(name="cargar", description="Carga un grafo de memoria de disco restaurando el entorno.")
    def _cargar(ruta: Optional[str] = None) -> Dict[str, Any]:
        return cargar(ruta)
    
    @mcp.tool(name="exportar", description="Exporta el grafo de memoria a documento Markdown legible.")
    def _exportar(ruta: str) -> Dict[str, Any]:
        return exportar(ruta)
