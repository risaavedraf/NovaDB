import logging
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .graph import NovaGraph, similitud_coseno
from .node import Node

logger = logging.getLogger(__name__)

class Rebalancer:
    """
    Rebalances the hierarchical graph by redistributing MEMORIA nodes
    across MEDIO nodes to maintain optimal search performance.
    """
    
    def __init__(self, graph: NovaGraph, 
                 desbalance_critico: float = 0.70,
                 ultimo_rebalanceo: Optional[datetime] = None):
        self.graph = graph
        self.desbalance_critico = desbalance_critico
        self.ultimo_rebalanceo = ultimo_rebalanceo or datetime.now()
    
    def necesita_rebalanceo(self) -> bool:
        """Check if rebalancing is needed (weekly or critical imbalance)."""
        dias_desde = (datetime.now() - self.ultimo_rebalanceo).days
        if dias_desde >= 7:
            logger.info("Weekly rebalance triggered (%d days since last)", dias_desde)
            return True
        
        balance = self._calcular_balance()
        if balance["balance_ratio"] < self.desbalance_critico:
            logger.warning("Critical imbalance detected (ratio: %.2f)", balance["balance_ratio"])
            return True
        
        return False
    
    def rebalancear(self) -> Dict[str, int]:
        """
        Execute rebalancing. Returns stats of what was changed.
        """
        if not self.necesita_rebalanceo():
            logger.debug("Rebalancing not needed")
            return {"fusionados": 0, "redistribuidos": 0}
        
        logger.info("Starting rebalancing...")
        stats = {"fusionados": 0, "redistribuidos": 0}
        
        medios = [n for n in self.graph.nodes.values() if n.tipo == "MEDIO"]
        if not medios:
            logger.info("No MEDIO nodes to rebalance")
            return stats
        
        grupo_ideal = self._grupo_ideal()
        
        sobrecargados = [m for m in medios if len(m.hijos) > grupo_ideal * 1.5]
        vacios = [m for m in medios if len(m.hijos) < 3]
        
        logger.info("Found %d overloaded, %d empty MEDIO nodes", 
                    len(sobrecargados), len(vacios))
        
        for vacio in vacios:
            try:
                if self._fusionar_medio(vacio):
                    stats["fusionados"] += 1
            except Exception as e:
                logger.error("Error fusing MEDIO %s: %s", vacio.id, e)
        
        for sobrecargado in sobrecargados:
            try:
                redistribuidos = self._redistribuir_medio(sobrecargado, grupo_ideal)
                stats["redistribuidos"] += redistribuidos
            except Exception as e:
                logger.error("Error redistributing MEDIO %s: %s", sobrecargado.id, e)
        
        self.graph.rebuild_indices()
        
        self.ultimo_rebalanceo = datetime.now()
        logger.info("Rebalancing complete: %s", stats)
        
        return stats
    
    def _grupo_ideal(self) -> int:
        """Calculate ideal group size."""
        n_memorias = sum(1 for n in self.graph.nodes.values() if n.tipo == "MEMORIA")
        n_medios = sum(1 for n in self.graph.nodes.values() if n.tipo == "MEDIO") or 1
        return max(3, int(math.sqrt(n_memorias) / n_medios))
    
    def _fusionar_medio(self, medio_vacio: Node) -> bool:
        """Merge an empty MEDIO into its closest sibling."""
        hermanos = []
        for pid in medio_vacio.padres:
            padre = self.graph.nodes.get(pid)
            if padre and padre.tipo == "MACRO":
                for hid in padre.hijos:
                    hermano = self.graph.nodes.get(hid)
                    if hermano and hermano.tipo == "MEDIO" and hermano.id != medio_vacio.id:
                        hermanos.append(hermano)
        
        if not hermanos:
            logger.debug("No siblings to merge %s into", medio_vacio.id)
            return False
        
        mejor = max(hermanos, key=lambda h: similitud_coseno(medio_vacio.vector, h.vector))
        
        for hijo_id in list(medio_vacio.hijos):
            hijo = self.graph.nodes.get(hijo_id)
            if hijo:
                medio_vacio.hijos.remove(hijo_id)
                if medio_vacio.id in hijo.padres:
                    hijo.padres.remove(medio_vacio.id)
                
                mejor.hijos.append(hijo_id)
                hijo.padres.append(mejor.id)
        
        for pid in list(medio_vacio.padres):
            padre = self.graph.nodes.get(pid)
            if padre and medio_vacio.id in padre.hijos:
                padre.hijos.remove(medio_vacio.id)
        
        del self.graph.nodes[medio_vacio.id]
        
        logger.info("Fused MEDIO %s into %s", medio_vacio.id, mejor.id)
        return True
    
    def _redistribuir_medio(self, sobrecargado: Node, grupo_ideal: int) -> int:
        """Redistribute children from overloaded MEDIO to siblings."""
        exceso = len(sobrecargado.hijos) - grupo_ideal
        if exceso <= 0:
            return 0
        
        hermanos = []
        for pid in sobrecargado.padres:
            padre = self.graph.nodes.get(pid)
            if padre and padre.tipo == "MACRO":
                for hid in padre.hijos:
                    hermano = self.graph.nodes.get(hid)
                    if hermano and hermano.tipo == "MEDIO" and hermano.id != sobrecargado.id:
                        hermanos.append(hermano)
        
        if not hermanos:
            return 0
        
        redistribuidos = 0
        hijos_ordenados = sorted(
            sobrecargado.hijos,
            key=lambda hid: self._distancia_promedio(hid, hermanos)
        )
        
        for hijo_id in hijos_ordenados[:exceso]:
            hijo = self.graph.nodes.get(hijo_id)
            if not hijo:
                continue
            
            mejor_hermano = min(
                hermanos,
                key=lambda h: 1 - similitud_coseno(hijo.vector, h.vector) if h.vector is not None else float('inf')
            )
            
            if hijo_id in sobrecargado.hijos:
                sobrecargado.hijos.remove(hijo_id)
            if sobrecargado.id in hijo.padres:
                hijo.padres.remove(sobrecargado.id)
            
            mejor_hermano.hijos.append(hijo_id)
            hijo.padres.append(mejor_hermano.id)
            
            redistribuidos += 1
        
        logger.info("Redistributed %d nodes from %s", redistribuidos, sobrecargado.id)
        return redistribuidos
    
    def _distancia_promedio(self, node_id: str, candidatos: List[Node]) -> float:
        """Calculate average distance from node to candidates."""
        nodo = self.graph.nodes.get(node_id)
        if not nodo or nodo.vector is None:
            return float('inf')
        
        distancias = [
            1 - similitud_coseno(nodo.vector, c.vector)
            for c in candidatos if c.vector is not None
        ]
        
        return sum(distancias) / len(distancias) if distancias else float('inf')
    
    def _calcular_balance(self) -> Dict[str, float]:
        """Calculate current balance metrics."""
        medios = [n for n in self.graph.nodes.values() if n.tipo == "MEDIO"]
        if not medios:
            return {"balance_ratio": 1.0}
        
        hijos_por_medio = [len(m.hijos) for m in medios]
        if not hijos_por_medio:
            return {"balance_ratio": 1.0}
        
        mean = sum(hijos_por_medio) / len(hijos_por_medio)
        variance = sum((x - mean) ** 2 for x in hijos_por_medio) / len(hijos_por_medio)
        ideal = self._grupo_ideal()
        ideal_variance = max(1, ideal * 0.1)
        balance_ratio = min(1.0, ideal_variance / (variance + 1))
        
        return {"balance_ratio": round(balance_ratio, 2)}
