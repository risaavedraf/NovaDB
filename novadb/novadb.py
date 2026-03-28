import os
import math
import logging
from typing import Dict, Any, List, Optional

import numpy as np

from novadb.core.node import Node
from novadb.core.graph import NovaGraph, DECAY_RATE_DEFAULT, RELEVANCIA_WEIGHT_DEFAULT, similitud_coseno
from novadb.core.search import HierarchicalSearch
from novadb.core.consolidator import Consolidator
from novadb.core.rebalancer import Rebalancer
from novadb.core.embedder import GeminiEmbedder, LocalEmbedder, BaseEmbedder
from novadb.storage import disk, exporter

logger = logging.getLogger(__name__)


class IncompatibleEmbedderError(ValueError):
    """
    Raised when the active embedder's vector dimensions don't match
    the dimensions stored in the database being loaded.
    """
    pass


class NovaDB:
    """
    Hierarchical Semantic Memory Engine.
    This is the only class that the Agent or the final application must instantiate and use.
    """

    def __init__(
        self, 
        embedder: Optional[BaseEmbedder] = None,
        path: str = "./db/nova.msgpack",
        autosave: bool = True,
        k_vecinos: int = 5,
        umbral_padre: float = 0.70,
        umbral_vecino: float = 0.65,
        access_boost: float = 0.15,
        decay_rate: float = DECAY_RATE_DEFAULT,
        relevancia_weight: float = RELEVANCIA_WEIGHT_DEFAULT,
        log_level: int = logging.INFO,
        log_file: Optional[str] = None
    ) -> None:
        from novadb.core.logging_config import setup_logging
        self.logger = setup_logging(level=log_level, log_file=log_file)
        
        self.path = path
        self.autosave = autosave
        self.k_vecinos = k_vecinos
        self.umbral_padre = umbral_padre
        self.umbral_vecino = umbral_vecino
        self.access_boost = access_boost
        self.decay_rate = decay_rate
        self.relevancia_weight = relevancia_weight
        
        if embedder is not None:
            self.embedder = embedder
        else:
            try:
                self.embedder = GeminiEmbedder()
                logger.info("Using GeminiEmbedder")
            except (ValueError, ImportError) as e:
                logger.warning("GeminiEmbedder failed (%s), falling back to LocalEmbedder", e)
                self.embedder = LocalEmbedder()
        
        if os.path.exists(self.path):
            if self.path.endswith('.json'):
                self.graph, saved_dims = disk.load_from_json(self.path)
            else:
                self.graph, saved_dims = disk.load_from_msgpack(self.path)
            self._validate_embedder_dims(saved_dims)
            self.graph.decay_rate = decay_rate
            self.graph.relevancia_weight = relevancia_weight
            self.graph.access_boost = access_boost
            self.graph.umbral_padre = umbral_padre
            self.graph.umbral_vecino = umbral_vecino
            self.graph.k_vecinos = k_vecinos
        else:
            self.graph = NovaGraph(
                k_vecinos=k_vecinos,
                decay_rate=decay_rate,
                relevancia_weight=relevancia_weight,
                access_boost=access_boost,
                umbral_padre=umbral_padre,
                umbral_vecino=umbral_vecino
            )
            
        self.searcher = HierarchicalSearch(self.graph)
        self.consolidator = Consolidator(self.graph, self.embedder, llm_namer=self._build_llm_namer())
        self.rebalancer = Rebalancer(self.graph)
        
    def _build_llm_namer(self):
        """Builds the LLM namer callback only if an API key exists. Returns None otherwise."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
            
            def llm_namer(textos: List[str]) -> str:
                fragmentos_str = "\n".join(f"- {t}" for t in textos)
                prompt = f"""Eres una IA analista ultra-racional estructurando información base de datos de conocimiento.
Revisa los siguientes fragmentos de memoria y responde ÚNICAMENTE con la categoría abstracta que los engloba a todos de manera natural.

Reglas:
1. MAXIMO 4 o 5 palabras.
2. NO me des explicaciones ni puntos finales.
3. Formato título (Ej: 'Decisiones Tecnológicas', 'Contexto de Proyectos', 'Detalles Personales').

Fragmentos:
{fragmentos_str}
"""
                response = client.models.generate_content(model=model_name, contents=prompt)
                return response.text.replace('**','').replace('"','').replace('.','').strip()
            
            return llm_namer
        except (ImportError, Exception) as e:
            logger.warning("LLM namer setup failed (%s), using offline naming", e)
            return None
    
    def _trigger_autosave(self) -> None:
        if self.autosave:
            self.save(self.path)

    # ==========================
    # WRITING
    # ==========================
    def insert(self, text: str, tipo: str = "MEMORIA", metadata: Dict[str, Any] = None) -> str:
        """Inserts a new readable record, vectorizes it, and anchors it to the graph."""
        vector = self.embedder.encode(text)
        node = Node(text=text, vector=vector, tipo=tipo, metadata=metadata or {})
        
        # 1. Mathematical insertion (MACRO/MEDIO/Neighbors connections)
        self.graph.insert(node)
        
        # 2. Self-organization Hook
        if tipo == "MEMORIA":
            self.consolidator.verificar_y_consolidar(node)
        
        # 3. Auto-rebalance check (weekly or critical imbalance)
        self._check_auto_rebalance()
            
        self._trigger_autosave()
        return node.id

    def connect(self, id_a: str, id_b: str, tipo_conexion: str, peso: float = 1.0) -> None:
        """Allows creating explicit connections that the mathematical system did not capture."""
        nodo_a = self.get(id_a)
        nodo_b = self.get(id_b)
        if not nodo_a or not nodo_b:
            raise ValueError("Uno o ambos IDs no existen en NovaDB.")
            
        # Unidirectional detailed connection (can be made bi-dir per agent design)
        nodo_a.conexiones.append({
            "target": id_b,
            "tipo": tipo_conexion,
            "peso": peso
        })
        self._trigger_autosave()

    def update(self, node_id: str, fields: Dict[str, Any]):
        """Updates the metadata or text of a node (re-embeds if text changes)"""
        nodo = self.get(node_id)
        if not nodo:
            return
            
        cambio_texto = "text" in fields and fields["text"] != nodo.text
        
        if cambio_texto:
            # 1. Unlink from current neighborhood to avoid creating Spatial Zombies
            for pid in nodo.padres:
                p = self.get(pid)
                if p and nodo.id in p.hijos: p.hijos.remove(nodo.id)
            for hid in nodo.hijos:
                h = self.get(hid)
                if h and nodo.id in h.padres: h.padres.remove(nodo.id)
            for vid in nodo.vecinos:
                v = self.get(vid)
                if v and nodo.id in v.vecinos: v.vecinos.remove(nodo.id)
                
            nodo.padres, nodo.hijos, nodo.vecinos = [], [], []
            
            # 2. Update the base content
            nodo.text = fields["text"]
            nodo.vector = self.embedder.encode(nodo.text)
            
            # 3. Re-insert to calculate its new mathematical position
            self.graph.insert(nodo)
            
            # 4. Potential consolidation of a new neighborhood
            if nodo.tipo == "MEMORIA":
                self.consolidator.verificar_y_consolidar(nodo)
        
        # 5. Auto-rebalance check (weekly or critical imbalance)
        self._check_auto_rebalance()
                
        if "metadata" in fields:
            nodo.metadata.update(fields["metadata"])
            
        self._trigger_autosave()

    # ==========================
    # READING
    # ==========================
    def search(self, query: str, n: int = 5) -> List[Dict[str, Any]]:
        """Search the graph by semantic similarity using O(sqrt(N))"""
        query_vector = self.embedder.encode(query)
        resultados_crudos = self.searcher.search(query_vector, top_k=n)
        
        # Format the output for the API
        response = []
        for nodo, sim in resultados_crudos:
            data = nodo.to_dict()
            # Remove massive vector to avoid overwhelming the consumer
            data.pop("vector", None) 
            data["_score"] = sim
            response.append(data)
            
        return response

    def get(self, node_id: str) -> Optional[Node]:
        """Retrieves the complete object including its vector"""
        return self.graph.get_node(node_id)

    def get_children(self, node_id: str) -> List[Dict[str, Any]]:
        """Retrieves all children of an organizer node"""
        padre = self.get(node_id)
        if not padre:
            return []
            
        hijos = []
        for hid in padre.hijos:
            h = self.graph.nodes.get(hid)
            if h:
                h_dict = h.to_dict()
                h_dict.pop("vector", None)
                hijos.append(h_dict)
        return hijos
        
    def _clean_node_dict(self, n_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to remove heavy mathematical fields before JSON serialization"""
        n_dict.pop("vector", None)
        return n_dict

    def get_context(self, node_id: str, depth: int = 2) -> Dict[str, Any]:
        """
        Retrieves the node and all its neighbors, ancestors, and descendants
        up to N levels to provide heavy "Mental Context" to an Agent.
        (Simplified version depth 1 for V1)
        """
        nodo = self.get(node_id)
        if not nodo:
            return {}
            
        return {
            "centro": self._clean_node_dict(nodo.to_dict()),
            "padres": [self._clean_node_dict(self.get(p).to_dict()) for p in nodo.padres if self.get(p)],
            "vecinos": [self._clean_node_dict(self.get(v).to_dict()) for v in nodo.vecinos if self.get(v)],
            "hijos": [self._clean_node_dict(self.get(h).to_dict()) for h in nodo.hijos if self.get(h)]
        }

    def olvidar(self, node_id: str) -> Dict[str, Any]:
        """
        Borrado quirúrgico del nodo indicado, sin cascada.
        Retorna los IDs de nodos MEMORIA que quedaron huérfanos.
        """
        huerfanos = self.graph.olvidar(node_id)
        if huerfanos is None:
            return {"success": False, "error": f"Nodo {node_id} no encontrado"}

        self._trigger_autosave()
        return {
            "success": True,
            "nodo_eliminado": node_id,
            "huerfanos": huerfanos,
            "total_huerfanos": len(huerfanos)
        }

    # ==========================
    # UTILIDADES API
    # ==========================
    def _validate_embedder_dims(self, saved_dims: int) -> None:
        """Raises IncompatibleEmbedderError if dims don't match the loaded DB."""
        if saved_dims is None:
            return  # Legacy DB with no dims metadata — skip validation
        current_dims = self.embedder.dims
        if current_dims is None:
            return  # Embedder doesn't report dims (custom) — skip
        if current_dims != saved_dims:
            raise IncompatibleEmbedderError(
                f"Embedder dimension mismatch: database was built with {saved_dims}-dim vectors, "
                f"but the current embedder produces {current_dims}-dim vectors. "
                f"Either use the same embedding model or re-build the database."
            )

    def save(self, path: Optional[str] = None) -> None:
        target = path or self.path
        dims = self.embedder.dims
        if target.endswith('.json'):
            disk.save_to_json(self.graph, target, embedding_dims=dims)
        else:
            disk.save_to_msgpack(self.graph, target, embedding_dims=dims)

    def load(self, path: Optional[str] = None) -> None:
        target = path or self.path
        if target.endswith('.json'):
            self.graph, saved_dims = disk.load_from_json(target)
        else:
            self.graph, saved_dims = disk.load_from_msgpack(target)

        self._validate_embedder_dims(saved_dims)

        # Re-instantiate consolidator to drop the old graph reference
        from novadb.core.consolidator import Consolidator
        self.consolidator = Consolidator(
            graph=self.graph,
            embedder=self.embedder,
            umbral_consolidacion=self.umbral_padre
        )

    def export_md(self, path: str) -> None:
        exporter.export_to_markdown(self.graph, path)

    def rebalancear(self) -> Dict[str, Any]:
        """
        Trigger manual rebalancing. Returns stats of what was changed.
        PRD Section 5.6: Redistributes MEMORIA nodes across MEDIO nodes.
        """
        resultado = self.rebalancer.rebalancear()
        if resultado["fusionados"] > 0 or resultado["redistribuidos"] > 0:
            self._trigger_autosave()
        return resultado

    def _check_auto_rebalance(self) -> None:
        """Auto-rebalance check on operations if enabled."""
        if self.rebalancer.necesita_rebalanceo():
            try:
                self.rebalancear()
            except Exception as e:
                logger.error("Auto-rebalance failed: %s", e)

    def _calcular_balance(self) -> Dict[str, Any]:
        """Calculate graph balance metrics (section 5.5)."""
        memorias = [n for n in self.graph.nodes.values() if n.tipo == "MEMORIA"]
        medios = [n for n in self.graph.nodes.values() if n.tipo == "MEDIO"]
        
        n_memorias = len(memorias)
        n_medios = len(medios) or 1
        grupo_ideal = int(math.sqrt(n_memorias)) if n_memorias > 0 else 0
        
        hijos_por_medio = [len(m.hijos) for m in medios]
        
        medio_sobrecargados = sum(1 for h in hijos_por_medio if h > grupo_ideal * 1.5)
        medio_vacios = sum(1 for h in hijos_por_medio if h < 3)
        
        if hijos_por_medio:
            variance = np.var(hijos_por_medio)
            ideal_variance = max(1, grupo_ideal * 0.1)
            balance_ratio = min(1.0, ideal_variance / (variance + 1))
        else:
            balance_ratio = 1.0
        
        return {
            "threshold_actual": self.consolidator.threshold_optimo(),
            "grupo_ideal": grupo_ideal,
            "balance_ratio": round(balance_ratio, 2),
            "medio_sobrecargados": medio_sobrecargados,
            "medio_vacios": medio_vacios,
            "rebalanceo_recomendado": balance_ratio < 0.70
        }

    def stats(self) -> Dict[str, Any]:
        """Radiografía completa del motor de conocimientos (PRD Section 8)."""
        total_nodos = self.graph.count()
        n_memorias = self.graph.count("MEMORIA")
        n_medios = self.graph.count("MEDIO")
        
        nodos_huerfanos = sum(
            1 for n in self.graph.nodes.values() 
            if n.tipo == "MEMORIA" and not any(
                self.graph.nodes.get(p) and self.graph.nodes[p].tipo == "MEDIO"
                for p in n.padres
            )
        )
        
        conexiones_totales = sum(
            len(n.padres) + len(n.hijos) + len(n.vecinos)
            for n in self.graph.nodes.values()
        )
        conexiones_horizontales = sum(len(n.vecinos) for n in self.graph.nodes.values())
        promedio_vecinos = round(conexiones_horizontales / total_nodos, 1) if total_nodos > 0 else 0.0
        
        nodo_mas_accedido = max(
            self.graph.nodes.values(), key=lambda n: n.accesos, default=None
        )
        nodo_mas_accedido_data = None
        if nodo_mas_accedido:
            nodo_mas_accedido_data = {
                "id": nodo_mas_accedido.id,
                "text": nodo_mas_accedido.text,
                "accesos": nodo_mas_accedido.accesos
            }
        
        relevancia_stats = self.graph.get_relevancia_stats()
        
        nodos_muy_relevantes = sum(
            1 for n in self.graph.nodes.values() if n.relevancia > 0.8
        )
        nodos_desatendidos = sum(
            1 for n in self.graph.nodes.values() if n.relevancia < 0.1
        )
        
        balance_metrics = self._calcular_balance()
        
        tamano_disco_mb = 0.0
        if os.path.exists(self.path):
            tamano_disco_mb = round(os.path.getsize(self.path) / (1024 * 1024), 2)
        
        ultima_consolidacion = None
        if self.consolidator.ultima_consolidacion:
            ultima_consolidacion = self.consolidator.ultima_consolidacion.isoformat()
        
        ultimo_rebalanceo = None
        if self.rebalancer.ultimo_rebalanceo:
            ultimo_rebalanceo = self.rebalancer.ultimo_rebalanceo.isoformat()
        
        return {
            "total_nodos": total_nodos,
            "por_tipo": {
                "MACRO": self.graph.count("MACRO"),
                "MEDIO": n_medios,
                "MEMORIA": n_memorias
            },
            "nodos_huerfanos": nodos_huerfanos,
            "conexiones_totales": conexiones_totales,
            "promedio_vecinos": promedio_vecinos,
            "nodo_mas_accedido": nodo_mas_accedido_data,
            "ultima_consolidacion": ultima_consolidacion,
            "ultimo_rebalanceo": ultimo_rebalanceo,
            "tamano_disco_mb": tamano_disco_mb,
            "threshold_actual": balance_metrics["threshold_actual"],
            "grupo_ideal": balance_metrics["grupo_ideal"],
            "balance_ratio": balance_metrics["balance_ratio"],
            "medio_sobrecargados": balance_metrics["medio_sobrecargados"],
            "medio_vacios": balance_metrics["medio_vacios"],
            "rebalanceo_recomendado": balance_metrics["rebalanceo_recomendado"],
            "decay_rate": self.decay_rate,
            "relevancia_weight": self.relevancia_weight,
            "nodos_muy_relevantes": nodos_muy_relevantes,
            "nodos_desatendidos": nodos_desatendidos,
            "relevancia_promedio": round(relevancia_stats["promedio"], 4)
        }
