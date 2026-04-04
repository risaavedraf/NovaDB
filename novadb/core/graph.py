import math
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from .node import Node

logger = logging.getLogger(__name__)

DECAY_RATE_DEFAULT = 0.0001
RELEVANCIA_WEIGHT_DEFAULT = 0.3

def similitud_coseno(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calculates the semantic similarity between two vectors.
    Returns a value between -1.0 (opposites) and 1.0 (identical).
    """
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    # Avoid division by zero for empty vectors
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))

class NovaGraph:
    """
    The underlying engine of NovaDB. Manages the node graph
    and the base operations for insertion and semantic connection.
    """
    def __init__(
        self,
        k_vecinos: int = 5,
        decay_rate: float = DECAY_RATE_DEFAULT,
        relevancia_weight: float = RELEVANCIA_WEIGHT_DEFAULT,
        access_boost: float = 0.15,
        umbral_padre: float = 0.70,
        umbral_vecino: float = 0.65
    ):
        self.nodes: Dict[str, Node] = {}
        self.k_vecinos = k_vecinos
        self.decay_rate = decay_rate
        self.relevancia_weight = relevancia_weight
        self.access_boost = access_boost
        self.umbral_padre = umbral_padre
        self.umbral_vecino = umbral_vecino

        self.indice_macro: Dict[str, Node] = {}
        self.indice_medio: Dict[str, List[Node]] = {}
        self.indice_memoria: Dict[str, List[Node]] = {}
        self.vector_cache: Dict[str, np.ndarray] = {}

    def update_relevancia_on_access(self, node: Node) -> None:
        """
        Boost relevancia on access using exponential moving average.
        The decay_factor represents how much weight to give to old value vs boost.
        Small decay_rate = slow decay = relevance persists longer.
        """
        now = datetime.now()
        time_since_last = (now - node.updated_at).total_seconds()
        hours_elapsed = time_since_last / 3600.0

        decay_factor = math.exp(-self.decay_rate * hours_elapsed)
        node.relevancia = min(1.0, node.relevancia * decay_factor + self.access_boost)
        node.accesos += 1
        node.updated_at = now
        logger.debug(f"Node {node.id} acceso #{node.accesos}, relevancia: {node.relevancia:.4f}")

    def apply_temporal_decay(self) -> None:
        """
        Apply decay to all nodes. Called periodically or during search
        to normalize relevancia across the graph.
        """
        now = datetime.now()
        for node in self.nodes.values():
            if node.vector is not None:
                hours_since = (now - node.updated_at).total_seconds() / 3600.0
                node.relevancia *= math.exp(-self.decay_rate * hours_since)
                node.updated_at = now

    def calculate_combined_score(self, cosine_sim: float, node: Node) -> float:
        """
        Combines cosine similarity with relevancia for ranking.
        """
        return (cosine_sim * (1.0 - self.relevancia_weight)) + (node.relevancia * self.relevancia_weight)

    def get_mas_relevante(self) -> Optional[Tuple[Node, float]]:
        """Returns the node with highest relevancia and its score."""
        if not self.nodes:
            return None
        _, node = max(self.nodes.items(), key=lambda x: x[1].relevancia)
        return (node, node.relevancia)

    def get_relevancia_stats(self) -> Dict[str, float]:
        """Returns statistics about relevancia distribution."""
        if not self.nodes:
            return {"promedio": 0.0, "max": 0.0, "min": 0.0}
        values = [n.relevancia for n in self.nodes.values() if n.vector is not None]
        if not values:
            return {"promedio": 0.0, "max": 0.0, "min": 0.0}
        return {
            "promedio": sum(values) / len(values),
            "max": max(values),
            "min": min(values)
        }

    def _actualizar_indice_nodo(self, node: Node) -> None:
        """Updates hierarchical indices when a node changes parents."""
        if node.tipo == "MACRO":
            self.indice_macro[node.id] = node
            return

        if node.tipo == "MEDIO":
            for padre_id in node.padres:
                if padre_id in self.indice_macro:
                    if padre_id not in self.indice_medio:
                        self.indice_medio[padre_id] = []
                    if node not in self.indice_medio[padre_id]:
                        self.indice_medio[padre_id].append(node)
            return

        if node.tipo == "MEMORIA":
            for padre_id in node.padres:
                padre = self.nodes.get(padre_id)
                if padre and padre.tipo == "MEDIO":
                    if padre_id not in self.indice_memoria:
                        self.indice_memoria[padre_id] = []
                    if node not in self.indice_memoria[padre_id]:
                        self.indice_memoria[padre_id].append(node)
            return

    def _agregar_a_indice(self, node: Node) -> None:
        """Adds a node to the hierarchical indices."""
        self.vector_cache[node.id] = node.vector

        if node.tipo == "MACRO":
            self.indice_macro[node.id] = node
            return

        if node.tipo == "MEDIO":
            for padre_id in node.padres:
                if padre_id not in self.indice_medio:
                    self.indice_medio[padre_id] = []
                if node not in self.indice_medio[padre_id]:
                    self.indice_medio[padre_id].append(node)
            return

        if node.tipo == "MEMORIA":
            for padre_id in node.padres:
                padre = self.nodes.get(padre_id)
                if padre and padre.tipo == "MEDIO":
                    if padre_id not in self.indice_memoria:
                        self.indice_memoria[padre_id] = []
                    if node not in self.indice_memoria[padre_id]:
                        self.indice_memoria[padre_id].append(node)

    def rebuild_indices(self) -> None:
        """Rebuilds all indices from scratch. Useful after load or desynchronization."""
        self.indice_macro.clear()
        self.indice_medio.clear()
        self.indice_memoria.clear()
        self.vector_cache.clear()

        for node in self.nodes.values():
            self.vector_cache[node.id] = node.vector

            if node.tipo == "MACRO":
                self.indice_macro[node.id] = node

            elif node.tipo == "MEDIO":
                for padre_id in node.padres:
                    if padre_id not in self.indice_medio:
                        self.indice_medio[padre_id] = []
                    self.indice_medio[padre_id].append(node)

            elif node.tipo == "MEMORIA":
                for padre_id in node.padres:
                    padre = self.nodes.get(padre_id)
                    if padre and padre.tipo == "MEDIO":
                        if padre_id not in self.indice_memoria:
                            self.indice_memoria[padre_id] = []
                        self.indice_memoria[padre_id].append(node)

    def invalidate_vector_cache(self, node_id: str) -> None:
        """Invalidates the vector cache for a specific node."""
        if node_id in self.vector_cache:
            del self.vector_cache[node_id]

    def get_cached_vector(self, node_id: str) -> Optional[np.ndarray]:
        """Gets a vector from cache or directly from the node."""
        if node_id in self.vector_cache:
            return self.vector_cache[node_id]
        node = self.nodes.get(node_id)
        if node:
            self.vector_cache[node_id] = node.vector
            return node.vector
        return None

    def insert(self, node: Node) -> str:
        """
        Inserts a node and semantically connects it to the existing graph.
        """
        self.nodes[node.id] = node
        self.vector_cache[node.id] = node.vector
        
        nodos_macro = list(self.indice_macro.values())
        if node.id in nodos_macro:
            nodos_macro = [n for n in nodos_macro if n.id != node.id]
        
        if node.tipo == "MACRO":
            self.indice_macro[node.id] = node
        elif node.tipo == "MEDIO" or node.tipo == "MEMORIA":
            if not node.padres:
                padre_encontrado = False
                
                if node.tipo == "MEMORIA":
                    for medio_list in self.indice_medio.values():
                        for medio in medio_list:
                            if medio.id != node.id:
                                sim = similitud_coseno(node.vector, medio.vector)
                                if sim >= self.umbral_padre:
                                    node.padres.append(medio.id)
                                    medio.hijos.append(node.id)
                                    padre_encontrado = True
                                    break
                        if padre_encontrado:
                            break
                    
                if not padre_encontrado and nodos_macro:
                    mejor_macro = max(nodos_macro, key=lambda n: similitud_coseno(node.vector, n.vector), default=None)
                    if mejor_macro and similitud_coseno(node.vector, mejor_macro.vector) >= self.umbral_padre:
                        node.padres.append(mejor_macro.id)
                        mejor_macro.hijos.append(node.id)
                        padre_encontrado = True
            
            if node.padres:
                self._agregar_a_indice(node)
        
        mismo_tipo = []
        if node.tipo == "MACRO":
            mismo_tipo = list(self.indice_macro.values())
        elif node.tipo == "MEDIO":
            for medio_list in self.indice_medio.values():
                mismo_tipo.extend(medio_list)
        elif node.tipo == "MEMORIA":
            for mem_list in self.indice_memoria.values():
                mismo_tipo.extend(mem_list)
        
        mismo_tipo = [n for n in mismo_tipo if n.id != node.id]
        
        if not mismo_tipo and node.tipo != "MACRO":
            mismo_tipo = [n for n in self.nodes.values() if n.tipo == node.tipo and n.id != node.id]
        
        vecinos_similitud = []
        for n in mismo_tipo:
            sim = similitud_coseno(node.vector, n.vector)
            if sim >= self.umbral_vecino:
                vecinos_similitud.append((n.id, sim))
                
        vecinos_similitud.sort(key=lambda x: x[1], reverse=True)
        top_vecinos = vecinos_similitud[:self.k_vecinos]
        
        for vec_id, _ in top_vecinos:
            node.vecinos.append(vec_id)
            vecino_node = self.nodes[vec_id]
            if node.id not in vecino_node.vecinos:
                vecino_node.vecinos.append(node.id)

        return node.id

    def count(self, tipo: Optional[str] = None) -> int:
        """Returns the total or filtered count of nodes in memory."""
        if not tipo:
            return len(self.nodes)
        return sum(1 for n in self.nodes.values() if n.tipo == tipo)

    def get_node(self, node_id: str) -> Optional[Node]:
        """Retrieves a node by exact UUID. Pure read — no side effects on relevancia."""
        return self.nodes.get(node_id)

    def olvidar(self, node_id: str) -> Optional[List[str]]:
        """
        Surgical deletion of the specified node, without cascade.

        1. Cleans all references to node_id in connected nodes:
           - In `padres` of each child node
           - In `hijos` of each parent node
           - In `vecinos` of each neighbor node
        2. Removes the node from the graph and indices.
        3. Returns the list of MEMORIA node IDs that became orphaned
           (without living MEDIO parents). Returns None if the node did not exist.
        """
        nodo = self.nodes.get(node_id)
        if nodo is None:
            return None

        # 1a. Clean reference in parents: remove node_id from hijos[]
        for padre_id in nodo.padres:
            padre = self.nodes.get(padre_id)
            if padre and node_id in padre.hijos:
                padre.hijos.remove(node_id)

        # 1b. Clean reference in children: remove node_id from padres[]
        for hijo_id in nodo.hijos:
            hijo = self.nodes.get(hijo_id)
            if hijo and node_id in hijo.padres:
                hijo.padres.remove(node_id)

        # 1c. Clean reference in neighbors: remove node_id from vecinos[]
        for vecino_id in nodo.vecinos:
            vecino = self.nodes.get(vecino_id)
            if vecino and node_id in vecino.vecinos:
                vecino.vecinos.remove(node_id)

        # 2. Remove from graph, indices, and cache
        del self.nodes[node_id]
        self.invalidate_vector_cache(node_id)

        # Clean from hierarchical indices
        self.indice_macro.pop(node_id, None)
        self.indice_medio.pop(node_id, None)
        self.indice_memoria.pop(node_id, None)

        # Also remove from lists within indices (in case it was a listed child)
        for medio_list in self.indice_medio.values():
            medio_list[:] = [m for m in medio_list if m.id != node_id]
        for mem_list in self.indice_memoria.values():
            mem_list[:] = [m for m in mem_list if m.id != node_id]

        # 3. Detect orphans: MEMORIA without living MEDIO parents
        huerfanos = []
        for n in self.nodes.values():
            if n.tipo == "MEMORIA":
                tiene_medio_vivo = any(
                    self.nodes.get(p) and self.nodes[p].tipo == "MEDIO"
                    for p in n.padres
                )
                if not tiene_medio_vivo:
                    huerfanos.append(n.id)

        return huerfanos
