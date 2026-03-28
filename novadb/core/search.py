import logging
import numpy as np
from typing import List, Tuple, Optional
from .node import Node
from .graph import NovaGraph, similitud_coseno

logger = logging.getLogger(__name__)

class HierarchicalSearch:
    """
    Structured search engine for NovaDB.
    Applies the MACRO -> MEDIO -> MEMORIA routing detailed in the
    architecture to scale without computational cost (O(sqrt(N))).
    """
    
    def __init__(self, graph: NovaGraph, umbral_medio: float = 0.65):
        self.graph = graph
        self.umbral_medio = umbral_medio
        
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[Node, float]]:
        """
        Traversal:
        1. Compares against MACROs.
        2. Descends to the best MEDIO (or expands to its neighbors if score is low).
        3. Collects MEMORIAs from the MEDIO and its borders (neighbors).
        4. Re-ranks by COMBINED similarity and updates access/relevancia.
        """
        nodos_macro = list(self.graph.indice_macro.values())
        
        if not nodos_macro:
            nodos_macro = [n for n in self.graph.nodes.values() if n.tipo == "MACRO"]
        
        if not nodos_macro:
            return self._busqueda_plana(query_vector, top_k)
            
        mejor_macro = self._get_mejor_nodo(query_vector, nodos_macro)
        if not mejor_macro:
            return self._busqueda_plana(query_vector, top_k)
        
        if not mejor_macro.hijos:
            return self._busqueda_plana(query_vector, top_k)
            
        hijos_macro = mejor_macro.hijos
        nodos_medio = [self.graph.nodes[nid] for nid in hijos_macro if nid in self.graph.nodes and self.graph.nodes[nid].tipo == "MEDIO"]
        
        if not nodos_medio:
            candidatos_directos = [self.graph.nodes[nid] for nid in hijos_macro if nid in self.graph.nodes and self.graph.nodes[nid].tipo == "MEMORIA"]
            if not candidatos_directos:
                return self._busqueda_plana(query_vector, top_k)
            frontera_ids = set([n.id for n in candidatos_directos])
        else:
            mejor_medio = self._get_mejor_nodo(query_vector, nodos_medio)
            
            if (not mejor_medio) or (similitud_coseno(query_vector, mejor_medio.vector) < self.umbral_medio):
                for vecino_id in mejor_macro.vecinos:
                    vecino_macro = self.graph.nodes.get(vecino_id)
                    if vecino_macro:
                        nodos_medio.extend([self.graph.nodes[h_id] for h_id in vecino_macro.hijos if h_id in self.graph.nodes and self.graph.nodes[h_id].tipo == "MEDIO"])
                mejor_medio = self._get_mejor_nodo(query_vector, nodos_medio)
                
            if not mejor_medio:
                return self._busqueda_plana(query_vector, top_k)
                
            frontera_ids = set(mejor_medio.hijos)
            
        for nid in list(frontera_ids): 
            nodo = self.graph.nodes.get(nid)
            if nodo:
                frontera_ids.update(nodo.vecinos)
                for conn in nodo.conexiones:
                    frontera_ids.add(conn["target"])
                
        candidatos_finales = [
            self.graph.nodes[nid] 
            for nid in frontera_ids 
            if nid in self.graph.nodes and self.graph.nodes[nid].tipo == "MEMORIA"
        ]
        
        resultados = []
        for nodo in candidatos_finales:
            sim = similitud_coseno(query_vector, nodo.vector)
            combined = self.graph.calculate_combined_score(sim, nodo)
            resultados.append((nodo, combined, sim))
            
        resultados.sort(key=lambda x: x[1], reverse=True)
        top_results = [(n, comb) for n, comb, sim in resultados[:top_k]]
        
        for nodo, _ in top_results:
            self.graph.update_relevancia_on_access(nodo)
            
        return top_results

    def _busqueda_plana(self, query_vector: np.ndarray, top_k: int) -> List[Tuple[Node, float]]:
        """Linear O(N) search. Used only at the beginning when there is no hierarchy."""
        resultados = []
        nodos_memoria = []
        for mem_list in self.graph.indice_memoria.values():
            nodos_memoria.extend(mem_list)
        
        if not nodos_memoria:
            nodos_memoria = [n for n in self.graph.nodes.values() if n.tipo == "MEMORIA"]
        
        for nodo in nodos_memoria:
            sim = similitud_coseno(query_vector, nodo.vector)
            combined = self.graph.calculate_combined_score(sim, nodo)
            resultados.append((nodo, combined, sim))
        
        resultados.sort(key=lambda x: x[1], reverse=True)
        top_results = [(n, comb) for n, comb, sim in resultados[:top_k]]
        for nodo, _ in top_results:
            self.graph.update_relevancia_on_access(nodo)
        return top_results
        
    def _get_mejor_nodo(self, query_vector: np.ndarray, nodos: List[Node]) -> Optional[Node]:
        """Calculates in isolation the best node at a specific level."""
        mejor_nodo = None
        mejor_sim = -1.0
        for nodo in nodos:
            sim = similitud_coseno(query_vector, nodo.vector)
            if sim > mejor_sim:
                mejor_sim = sim
                mejor_nodo = nodo
        return mejor_nodo
