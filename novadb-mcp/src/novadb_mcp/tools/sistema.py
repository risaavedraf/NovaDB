"""
NovaDB MCP Tools - Sistema

Tools for system stats and maintenance.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import logging
from typing import Dict, Any

from ..serializers import serialize_stats
from ..config import get_config

logger = logging.getLogger(__name__)


def get_db():
    """Get NovaDB instance from memoria module."""
    from .memoria import get_db as _get_db
    return _get_db()


def analizar() -> Dict[str, Any]:
    """
    Obtiene estadísticas del grafo de memoria.
    
    Returns:
        Métricas completas del sistema de memoria
    """
    try:
        db = get_db()
        stats = db.stats()
        return {
            "success": True,
            "stats": serialize_stats(stats)
        }
    except Exception as e:
        logger.error("Error analyzing: %s", e)
        return {"success": False, "error": str(e)}


def consolidar(umbral: float = 0.70) -> Dict[str, Any]:
    """
    Ejecuta consolidación masiva de nodos huérfanos.
    Delega al Consolidator del core.
    
    Args:
        umbral: Similitud mínima para agrupar (0.0-1.0, default: 0.70)
    
    Returns:
        Resultado de la consolidación con grupos creados
    """
    try:
        db = get_db()
        resultado = db.consolidator.consolidar_masivo(umbral)
        
        if resultado["grupos_creados"] > 0:
            db.save(get_config().db_path)
        
        return {
            "success": True,
            "huerfanos_antes": resultado["huerfanos"],
            "grupos_encontrados": resultado["grupos_encontrados"],
            "grupos_creados": resultado["grupos_creados"],
            "medios_creados": resultado["creados"],
            "message": f"✅ {resultado['grupos_creados']} grupos consolidados de {resultado['huerfanos']} huérfanos"
        }
    except Exception as e:
        logger.error("Error consolidating: %s", e)
        return {"success": False, "error": str(e)}


def rebalancear() -> Dict[str, Any]:
    """
    Fuerza un rebalanceo del grafo de memoria.
    Reorganiza nodos MEDIO sobrecargados y fusiona vacíos.
    
    Returns:
        Resultado del rebalanceo
    """
    try:
        db = get_db()
        result = db.rebalancear()
        db.save(get_config().db_path)
        return {
            "success": True,
            "result": result,
            "message": "✅ Grafo rebalanceado"
        }
    except Exception as e:
        logger.error("Error rebalancing: %s", e)
        return {"success": False, "error": str(e)}


def register(mcp):
    @mcp.tool(name="analizar", description="Obtiene estadísticas completas del grafo de memoria.")
    def _analizar() -> Dict[str, Any]:
        return analizar()
    
    @mcp.tool(name="consolidar", description="Consolida nodos huérfanos en categorías MEDIO automáticamente.")
    def _consolidar(umbral: float = 0.70) -> Dict[str, Any]:
        """Consolida nodos huérfanos en categorías MEDIO automáticamente."""
        return consolidar(umbral)
    
    @mcp.tool(name="rebalancear", description="Fuerza un rebalanceo del grafo de memoria y reorganiza nodos.")
    def _rebalancear() -> Dict[str, Any]:
        return rebalancear()