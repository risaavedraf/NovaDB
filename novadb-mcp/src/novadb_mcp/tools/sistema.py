"""
NovaDB MCP Tools - Sistema

Tools for system stats and maintenance.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import logging
from typing import Dict, Any, Optional

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


def consolidar_proponer(umbral: float = 0.82) -> Dict[str, Any]:
    """
    FASE 1: Propone agrupaciones semánticas de nodos huérfanos sin alterar la DB.
    
    Args:
        umbral: Similitud mínima para agrupar (Default: 0.82)
    """
    try:
        db = get_db()
        resultado = db.consolidar_proponer(umbral)
        return {
            "success": True,
            "huerfanos": resultado["huerfanos"],
            "grupos_propuestos": resultado["grupos"],
            "message": f"Se proponen {len(resultado['grupos'])} grupos a partir de {resultado['huerfanos']} huérfanos. Revisa los nombres sugeridos y usa 'consolidar_ejecutar' enviando los IDs de los nodos que deseas agrupar y su nombre real."
        }
    except Exception as e:
        logger.error("Error proponiendo consolidación: %s", e)
        return {"success": False, "error": str(e)}

def consolidar_ejecutar(nodo_ids: list[str], nombre: str) -> Dict[str, Any]:
    """
    FASE 2: Ejecuta la consolidación creando un nodo MEDIO con el nombre proporcionado.
    
    Args:
        nodo_ids: Lista de IDs de nodos MEMORIA a agrupar.
        nombre: Nombre que se pondrá al nodo MEDIO.
    """
    try:
        db = get_db()
        grupos_input = [{"nodo_ids": nodo_ids, "nombre": nombre}]
        resultado = db.consolidar_ejecutar(grupos_input)
        
        if resultado["grupos_creados"] > 0:
            db.save(get_config().db_path)
            
        return {
            "success": True,
            "grupos_creados": resultado["grupos_creados"],
            "creados": resultado["creados"],
            "errores": resultado["errores"],
            "message": f"✅ Creado nodo MEDIO '{nombre}' agrupando {len(nodo_ids)} memorias." if resultado["grupos_creados"] > 0 else "❌ No se pudo crear el grupo."
        }
    except Exception as e:
        logger.error("Error al ejecutar consolidación: %s", e)
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


def fisionar(medio_id: str, k: Optional[int] = None) -> Dict[str, Any]:
    """
    Divide un nodo MEDIO sobrecargado en K nodos MEDIO usando K-Means (mitosis).
    Útil cuando un nodo acumula demasiados hijos y no tiene hermanos a quienes redistribuir.

    Args:
        medio_id: ID del nodo MEDIO a dividir.
        k:        Nº de clusters (None = calculado automáticamente por el motor).

    Returns:
        Resultado con los nuevos nodos MEDIO creados.
    """
    try:
        db = get_db()
        result = db.fisionar(medio_id, k=k)
        if result.get("success"):
            db.save(get_config().db_path)
        return result
    except Exception as e:
        logger.error("Error fisionando nodo %s: %s", medio_id, e)
        return {"success": False, "error": str(e)}


def register(mcp):
    @mcp.tool(name="analizar", description="Obtiene estadísticas completas del grafo de memoria.")
    def _analizar() -> Dict[str, Any]:
        return analizar()
    
    @mcp.tool(name="consolidar_proponer", description="FASE 1: Propuesta. Busca nodos huérfanos superpuestos semánticamente y propone clusters para convertirlos en grupos MEDIO, SIN afectar el grafo. Devuelve listas de nodos y nombres sugeridos.")
    def _consolidar_proponer(umbral: float = 0.82) -> Dict[str, Any]:
        return consolidar_proponer(umbral)

    @mcp.tool(name="consolidar_ejecutar", description="FASE 2: Ejecución. Recibe una lista de IDs de nodos huérfanos y un 'nombre' descriptivo humano, y los agrupa creando y conectando un nodo MEDIO a su MACRO de forma definitiva.")
    def _consolidar_ejecutar(nodo_ids: list[str], nombre: str) -> Dict[str, Any]:
        return consolidar_ejecutar(nodo_ids, nombre)
    
    @mcp.tool(name="rebalancear", description="Fuerza un rebalanceo del grafo de memoria y reorganiza nodos.")
    def _rebalancear() -> Dict[str, Any]:
        return rebalancear()

    @mcp.tool(
        name="fisionar",
        description=(
            "Divide un nodo MEDIO sobrecargado en K nodos MEDIO usando K-Means interno (mitosis). "
            "Usa esto cuando un MEDIO tiene demasiados hijos y no tiene hermanos a quienes redistribuir. "
            "Provee el ID del nodo MEDIO a dividir. El parámetro 'k' es opcional (por defecto se calcula automáticamente)."
        )
    )
    def _fisionar(medio_id: str, k: Optional[int] = None) -> Dict[str, Any]:
        return fisionar(medio_id, k)