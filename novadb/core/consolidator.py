import math
import logging
import re
from collections import Counter
from datetime import datetime
from typing import List, Optional, Callable, Dict, Any
from novadb.core.node import Node
from novadb.core.graph import NovaGraph, similitud_coseno
from novadb.core.embedder import BaseEmbedder

logger = logging.getLogger(__name__)

# Embedded stopwords (Spanish + English) for offline naming
_STOPWORDS = frozenset(
    # Español
    "de la que el en y a los del se las por un para con no una su al lo como "
    "más pero sus le ya o este sí porque esta entre cuando muy sin sobre "
    "también me hasta hay donde quien desde todo nos durante todos uno "
    "les ni contra otros ese eso ante esos algunos unos yo otro otras otra "
    "él tanto estos mucho quien nada muchos cual sea poco este estar "
    # Inglés
    "the be to of and a in that have i it for not on with he as you do at "
    "this but his by from they we say her she or an will my one all would "
    "there their what so up out if about who get which go me when make can "
    "like time no just him know take people into year your good some could "
    "them see other than then now look only come its over think also back "
    "after use two how our work first well way even new want because any "
    "these give day most us is are was were been has had do does did will "
    "shall may might must can could would should".split()
)

# Type for optional LLM naming callback (injected from outside)
LlmNamer = Callable[[List[str]], str]


class Consolidator:
    """
    Intelligent sub-system responsible for NovaDB's "Magic".
    Detects loose memory accumulations and creates categories (MEDIO).

    By default uses offline naming (keyword extraction).
    Optionally accepts an `llm_namer` callback for external LLM naming.
    """
    def __init__(
        self,
        graph: NovaGraph,
        embedder: BaseEmbedder,
        umbral_consolidacion: float = 0.75,
        llm_namer: Optional[LlmNamer] = None,
    ) -> None:
        self.graph = graph
        self.embedder = embedder
        self.umbral_consolidacion = umbral_consolidacion
        self.llm_namer = llm_namer
        self.ultima_consolidacion = None
        
    def threshold_optimo(self) -> int:
        """Calculates the optimal number of orphan nodes before consolidating (Mathematical auto-balance)"""
        n_memorias = self.graph.count(tipo="MEMORIA")
        n_medio = self.graph.count(tipo="MEDIO") or 1
        
        grupo_ideal = math.sqrt(n_memorias) if n_memorias > 0 else 0
        threshold = int(grupo_ideal / n_medio)
        
        return max(3, min(20, threshold))
        
    def verificar_y_consolidar(self, nuevo_nodo: Node) -> Optional[Node]:
        """
        This hook must be called after each MEMORIA insert.
        """
        if nuevo_nodo.tipo != "MEMORIA":
            return None
            
        padres_medio = [p for p in nuevo_nodo.padres if self.graph.nodes.get(p) and self.graph.nodes[p].tipo == "MEDIO"]
        if padres_medio:
            return None
            
        huerfanos = []
        for n in self.graph.nodes.values():
            if n.tipo == "MEMORIA" and n.id != nuevo_nodo.id:
                padres_medio = [p_id for p_id in n.padres if self.graph.nodes.get(p_id) and self.graph.nodes[p_id].tipo == "MEDIO"]
                if not padres_medio:
                    huerfanos.append(n)
        
        grupo = [nuevo_nodo]
        for h in huerfanos:
            if similitud_coseno(nuevo_nodo.vector, h.vector) >= self.umbral_consolidacion:
                grupo.append(h)
                
        if len(grupo) >= self.threshold_optimo():
            return self._ejecutar_consolidacion(grupo)
            
        return None
        
    def _nombrar_grupo_offline(self, textos: List[str]) -> str:
        """
        Offline naming via keyword extraction.
        Tokenizes, filters stopwords, picks top-3 most frequent words.
        Fallback: "Untitled Group {timestamp}" if no decent keywords found.
        """
        # 1. Tokenize all texts
        palabras: List[str] = []
        for texto in textos:
            tokens = re.findall(r'[a-zA-ZáéíóúñüÁÉÍÓÚÑÜ]+', texto.lower())
            palabras.extend(t for t in tokens if t not in _STOPWORDS and len(t) > 2)

        if not palabras:
            return f"Untitled Group {datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 2. Top-3 most frequent words
        conteo = Counter(palabras)
        top_keywords = [w.capitalize() for w, _ in conteo.most_common(3)]

        if not top_keywords:
            return f"Untitled Group {datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 3. Join → MEDIO name
        return " ".join(top_keywords)

    def _nombrar_grupo(self, textos: List[str]) -> str:
        """
        Determines the group name.
        Uses LLM callback if injected; otherwise falls back to offline naming.
        """
        if self.llm_namer:
            try:
                nombre = self.llm_namer(textos)
                if nombre and nombre.strip():
                    return nombre.strip()
            except Exception:
                logger.warning("LLM namer failed, falling back to offline naming", exc_info=True)

        return self._nombrar_grupo_offline(textos)

    def consolidar_masivo(self, umbral: Optional[float] = None) -> Dict[str, Any]:
        """
        Consolidación masiva de todos los huérfanos del grafo.
        Usa el umbral de similitud pasado o el de instancia.
        
        Returns:
            Dict con cantidad de huérfanos procesados, grupos encontrados, grupos creados.
        """
        threshold = umbral if umbral is not None else self.umbral_consolidacion
        
        huerfanos = [
            n for n in self.graph.nodes.values()
            if n.tipo == "MEMORIA" and not any(
                self.graph.nodes.get(p) and self.graph.nodes[p].tipo == "MEDIO"
                for p in n.padres
            )
        ]
        
        if not huerfanos:
            return {"huerfanos": 0, "grupos_encontrados": 0, "grupos_creados": 0, "creados": []}
        
        grupos: List[List[Node]] = []
        usados = set()
        
        for h in huerfanos:
            if h.id in usados:
                continue
            grupo = [h]
            usados.add(h.id)
            
            for otro in huerfanos:
                if otro.id in usados:
                    continue
                if h.vector is not None and otro.vector is not None:
                    if similitud_coseno(h.vector, otro.vector) >= threshold:
                        grupo.append(otro)
                        usados.add(otro.id)
            
            if len(grupo) >= self.threshold_optimo():
                grupos.append(grupo)
        
        creados = []
        for grupo in grupos:
            nodo = self._ejecutar_consolidacion(grupo)
            if nodo:
                creados.append(nodo)
        
        return {
            "huerfanos": len(huerfanos),
            "grupos_encontrados": len(grupos),
            "grupos_creados": len(creados),
            "creados": [{"id": n.id, "text": n.text} for n in creados]
        }
        
    def _ejecutar_consolidacion(self, grupo: List[Node]) -> Optional[Node]:
        textos = [n.text for n in grupo]
        concepto = self._nombrar_grupo(textos)

        try:
            vector_concepto = self.embedder.encode(concepto)

            nuevo_medio = Node(
                text=concepto,
                vector=vector_concepto,
                tipo="MEDIO"
            )

            nuevo_medio.metadata["auto_consolidated"] = True
            nuevo_medio.metadata["grupo_size"] = len(grupo)
            nuevo_medio.metadata["naming_mode"] = "llm" if self.llm_namer else "offline"

            self.graph.insert(nuevo_medio)

            for nodo in grupo:
                for pid in list(nodo.padres):
                    padre_viejo = self.graph.nodes.get(pid)
                    if padre_viejo and padre_viejo.tipo == "MACRO":
                        nodo.padres.remove(pid)
                        if nodo.id in padre_viejo.hijos:
                            padre_viejo.hijos.remove(nodo.id)

                nodo.padres.append(nuevo_medio.id)
                nuevo_medio.hijos.append(nodo.id)

            self.graph.rebuild_indices()
            self.ultima_consolidacion = datetime.now()
            logger.info(f"Consolidation completed: {concepto} with {len(grupo)} memories at {self.ultima_consolidacion}")
            return nuevo_medio

        except Exception as e:
            logger.error("Consolidation failed", exc_info=True)
            return None
