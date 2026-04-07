import logging
import math
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np

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
                # Si redistribución no movió nada (sin hermanos), aplicar mitosis
                if redistribuidos == 0 and len(sobrecargado.hijos) > grupo_ideal * 1.5:
                    logger.info("No siblings found for %s — triggering mitosis", sobrecargado.id)
                    nuevos = self.mitosis(sobrecargado)
                    stats["redistribuidos"] += len(nuevos)
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

    # ──────────────────────────────────────────────────────────────
    # MITOSIS — División celular de un MEDIO sobrecargado
    # ──────────────────────────────────────────────────────────────

    def mitosis(self, medio: Node, k: Optional[int] = None, max_iters: int = 20) -> List[Node]:
        """
        Divide un nodo MEDIO sobrecargado en K nuevos nodos MEDIO.

        Algoritmo:
          1. Determina K automáticamente si no se provee (ceil(hijos / grupo_ideal)).
          2. Inicializa K centroides eligiendo K hijos al azar.
          3. Itera asignaciones: cada hijo va al centroide más cercano (cosine).
          4. Recalcula centroides como promedio aritmético de sus miembros.
          5. Al converger, crea K nuevos nodos MEDIO y reasigna hijos.
          6. Elimina el MEDIO original del grafo.

        Args:
            medio:     Nodo MEDIO a dividir (debe tener ≥ 4 hijos con vectores).
            k:         Número de divisiones. Si None, se calcula automáticamente.
            max_iters: Límite de iteraciones K-Means.

        Returns:
            Lista de nuevos nodos MEDIO creados. Vacía si la mitosis no pudo ocurrir.
        """
        hijos = [
            self.graph.nodes[hid]
            for hid in medio.hijos
            if hid in self.graph.nodes and self.graph.nodes[hid].vector is not None
        ]

        if len(hijos) < 4:
            logger.warning("Mitosis aborted: MEDIO %s has fewer than 4 valid children", medio.id)
            return []

        grupo_ideal = self._grupo_ideal()
        if k is None:
            k = max(2, math.ceil(len(hijos) / max(grupo_ideal, 1)))
        k = min(k, len(hijos))  # k nunca puede superar al número de hijos

        logger.info("Starting mitosis on MEDIO '%s' (%d hijos → %d clusters)",
                    medio.text[:40], len(hijos), k)

        # ── 1. Inicializar centroides (K-Means++ simplificado: primero aleatorio, resto max-dist) ──
        centroides: List[List[float]] = [list(hijos[random.randrange(len(hijos))].vector)]
        for _ in range(k - 1):
            distancias_max = [
                min(1 - similitud_coseno(h.vector, c) for c in centroides)
                for h in hijos
            ]
            idx = distancias_max.index(max(distancias_max))
            centroides.append(list(hijos[idx].vector))

        # ── 2. Iteraciones K-Means ──
        asignaciones: List[int] = [0] * len(hijos)
        for _ in range(max_iters):
            nueva_asignacion: List[int] = []
            for hijo in hijos:
                sims = [similitud_coseno(hijo.vector, c) for c in centroides]
                nueva_asignacion.append(sims.index(max(sims)))

            if nueva_asignacion == asignaciones:
                break  # convergió
            asignaciones = nueva_asignacion

            # Recalcular centroides
            for ci in range(k):
                miembros = [hijos[i].vector for i, a in enumerate(asignaciones) if a == ci]
                if miembros:
                    dim = len(miembros[0])
                    nuevo_centroide = [sum(v[d] for v in miembros) / len(miembros) for d in range(dim)]
                    centroides[ci] = nuevo_centroide

        # Agrupar hijos por cluster
        clusters: List[List[Node]] = [[] for _ in range(k)]
        for i, hijo in enumerate(hijos):
            clusters[asignaciones[i]].append(hijo)

        # Descartar clusters vacíos
        clusters = [c for c in clusters if c]

        if len(clusters) < 2:
            logger.warning("Mitosis produced only 1 cluster — aborting to avoid infinite loop")
            return []

        # ── 3. Crear nuevos nodos MEDIO por cluster ──
        # Identificar padres MACRO del original (para heredar)
        macros_padres = [
            self.graph.nodes[pid]
            for pid in medio.padres
            if pid in self.graph.nodes and self.graph.nodes[pid].tipo == "MACRO"
        ]

        nuevos_medios: List[Node] = []
        for idx, cluster in enumerate(clusters):
            dim = len(cluster[0].vector)
            vector_cluster = np.array([sum(n.vector[d] for n in cluster) / len(cluster) for d in range(dim)], dtype=np.float32)
            
            # Normalizar para que cosine_sim trabaje bien visualmente y guardar como floats estándar
            norm = np.linalg.norm(vector_cluster)
            if norm > 0:
                vector_cluster = vector_cluster / norm
            vector_cluster_flat = [float(v) for v in vector_cluster]

            # Nombre automático: tomamos las primeras palabras del hijo más relevante
            nombre_base = medio.text.strip()
            nombre_nuevo = f"{nombre_base} [{idx + 1}/{len(clusters)}]"

            nuevo = Node(
                text=nombre_nuevo,
                vector=vector_cluster_flat,
                tipo="MEDIO"
            )
            nuevo.metadata["mitosis"] = True
            nuevo.metadata["origen_id"] = medio.id
            nuevo.metadata["cluster_size"] = len(cluster)

            self.graph.insert(nuevo)

            # Reasignar hijos
            for hijo in cluster:
                # Remover vínculo con el MEDIO original
                if medio.id in hijo.padres:
                    hijo.padres.remove(medio.id)
                # Agregar vínculo con el nuevo MEDIO
                if nuevo.id not in hijo.padres:
                    hijo.padres.append(nuevo.id)
                if hijo.id not in nuevo.hijos:
                    nuevo.hijos.append(hijo.id)

            # Conectar nuevo MEDIO SOLO al MACRO más similar semánticamente para evitar singularidades visuales
            mejor_macro = None
            mejor_sim = -1
            for macro in macros_padres:
                if macro.vector is None: continue
                sim = float(np.dot(vector_cluster, np.array(macro.vector, dtype=np.float32)))
                if sim > mejor_sim:
                    mejor_sim = sim
                    mejor_macro = macro
            
            if mejor_macro:
                if nuevo.id not in mejor_macro.hijos:
                    mejor_macro.hijos.append(nuevo.id)
                if mejor_macro.id not in nuevo.padres:
                    nuevo.padres.append(mejor_macro.id)
            elif macros_padres: # Fallback seguro
                macro_fb = macros_padres[0]
                if nuevo.id not in macro_fb.hijos:
                    macro_fb.hijos.append(nuevo.id)
                if macro_fb.id not in nuevo.padres:
                    nuevo.padres.append(macro_fb.id)

            nuevos_medios.append(nuevo)
            logger.info("Mitosis cluster %d/%d: MEDIO '%s' with %d hijos",
                        idx + 1, len(clusters), nombre_nuevo, len(cluster))

        # ── 4. Eliminar el MEDIO original ──
        # Desconectar de MACROs
        for macro in macros_padres:
            if medio.id in macro.hijos:
                macro.hijos.remove(medio.id)
        # Eliminar del grafo
        if medio.id in self.graph.nodes:
            del self.graph.nodes[medio.id]

        self.graph.rebuild_indices()
        logger.info("Mitosis complete: MEDIO '%s' → %d new nodes", medio.text[:40], len(nuevos_medios))

        return nuevos_medios

    def fisionar(self, medio_id: str, k: Optional[int] = None) -> Dict:
        """
        API pública de mitosis por ID. Para uso desde herramientas MCP.

        Args:
            medio_id: ID del nodo MEDIO a dividir.
            k:        Número de divisiones (None = auto).

        Returns:
            Dict con resultado y nuevos nodos creados.
        """
        nodo = self.graph.nodes.get(medio_id)
        if nodo is None:
            return {"success": False, "error": f"Nodo {medio_id} no encontrado"}
        if nodo.tipo != "MEDIO":
            return {"success": False, "error": f"El nodo {medio_id} no es de tipo MEDIO (es {nodo.tipo})"}

        nuevos = self.mitosis(nodo, k=k)

        if not nuevos:
            return {
                "success": False,
                "error": "La mitosis no pudo ejecutarse (insuficientes hijos con vectores o k=1)"
            }

        return {
            "success": True,
            "original_id": medio_id,
            "clusters_creados": len(nuevos),
            "nuevos_medios": [
                {"id": n.id, "text": n.text, "hijos": len(n.hijos)}
                for n in nuevos
            ]
        }
    
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
