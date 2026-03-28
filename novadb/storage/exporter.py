import os
from datetime import datetime
from typing import List, Optional
from novadb.core.graph import NovaGraph
from novadb.core.node import Node

def export_to_markdown(graph: NovaGraph, path: str) -> None:
    """
    Exporta el Knowledge Graph actual a un archivo Markdown estructurado
    por niveles jerárquicos (MACRO -> MEDIO -> MEMORIA) y huérfanos.
    """
    directorio = os.path.dirname(os.path.abspath(path))
    if directorio:
        os.makedirs(directorio, exist_ok=True)
        
    lineas = [
        f"# NovaDB: Mapa de Conocimiento Exportado",
        f"_Generado: {datetime.now().isoformat()}_",
        f"\n**Métricas Totales:**",
        f"- Nodos totales: {graph.count()}",
        f"- MACRO: {graph.count('MACRO')}",
        f"- MEDIO: {graph.count('MEDIO')}",
        f"- MEMORIA: {graph.count('MEMORIA')}",
        "\n---\n"
    ]
    
    # Separamos los nodos para armar el arbol top-down
    macros = [n for n in graph.nodes.values() if n.tipo == "MACRO"]
    medios_libres = [n for n in graph.nodes.values() if n.tipo == "MEDIO" and not getattr(n, 'padres', [])]
    memorias_huerfanas = [n for n in graph.nodes.values() if n.tipo == "MEMORIA" and not getattr(n, 'padres', [])]

    def render_memoria(mem_id: str, prefijo: str = "") -> None:
        mem: Optional[Node] = graph.nodes.get(mem_id)
        if mem:
            conectividad = len(mem.vecinos)
            lineas.append(f"{prefijo}- {mem.text} _(H: {mem.accesos} | V: {conectividad})_")

    def render_medio(medio_id: str, prefijo: str = "") -> None:
        med: Optional[Node] = graph.nodes.get(medio_id)
        if med:
            lineas.append(f"{prefijo}### 📌 {med.text} [MEDIO]")
            for h_id in med.hijos:
                h = graph.nodes.get(h_id)
                if h and h.tipo == "MEMORIA":
                    render_memoria(h_id, prefijo)
                    
    # Render completo de jerarquías que nacen desde un MACRO
    for macro in macros:
        lineas.append(f"## 🏛️ {macro.text.upper()} [MACRO]")
        for h_id in macro.hijos:
            h = graph.nodes.get(h_id)
            if h:
                if h.tipo == "MEDIO":
                    render_medio(h.id, "")
                elif h.tipo == "MEMORIA":
                    # Fallback natural (MEMORIA directa al MACRO)
                    render_memoria(h.id, "")
        lineas.append("\n---\n")
        
    # Render de capas MEDIAS que nacieron solas pero aún no tienen MACRO (raro pero posible)
    if medios_libres:
        lineas.append("## 🚧 CONCEPTOS EN DESARROLLO (MEDIOS SIN MACRO)")
        for med in medios_libres:
            render_medio(med.id, "")
        lineas.append("\n---\n")
        
    # Render de las memorias huérfanas esperando consolidación automática
    if memorias_huerfanas:
        lineas.append("## ☁️ MEMORIAS HUERFANAS (Fragmentos Sueltos)")
        for mem in memorias_huerfanas:
            render_memoria(mem.id, "")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
