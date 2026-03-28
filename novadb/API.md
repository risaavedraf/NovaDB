# NovaDB - Documentación de API Pública

La fachada de la base de datos matemática es la clase `NovaDB`, ubicada en `novadb.py`.

## 🚀 Inicialización

```python
from novadb.novadb import NovaDB
from novadb.core.embedder import GeminiEmbedder

db = NovaDB(
    embedder=GeminiEmbedder(),
    path="./db/nova.msgpack",
    autosave=True,
    decay_rate=0.01,           # decaimiento por hora (None = disabled)
    relevancia_weight=0.30,    # peso de relevancia en re-rankeo
    access_boost=0.10,         # boost por acceso (capped +50%)
    log_level="INFO",          # DEBUG | INFO | WARNING | ERROR
    log_file=None             # None = stdout, o ruta a archivo .log
)
```

## ✍️ Métodos de Escritura

### `insert(text: str, tipo: str = "MEMORIA", metadata: dict | None = None) -> str`
Inserta un nuevo contenido lógico. NovaDB vectoriza el texto, lo coloca semánticamente en el barrio mental correcto y maneja las consolidaciones jerárquicas en segundo plano.

### `connect(id_a: str, id_b: str, tipo_conexion: str, peso: float = 1.0) -> None`
Añade un puente explícito y forzado entre dos nodos. Útil cuando se quieren cruzar conceptos a pesar de que el vector matemático no indique una similitud geométrica alta.

### `update(node_id: str, fields: dict[str, Any]) -> None`
Reescribe la metainformación o el `text` de un nodo. Si el `text` cambia, la posición matemática del nodo en el grafo es despegada, re-vectorizada y recalculada para evitar problemas de Nodos Zombie.

## 🔭 Métodos de Lectura

### `search(query: str, n: int = 5) -> list[dict]`
Entrega los `n` nodos de tipo `MEMORIA` más coherentes con tu query. 
- Usa ruteo interno **O(√N)** con índices jerárquicos
- Re-rankeo: `cosine_similarity * 0.7 + relevancia * 0.3`
- La `relevancia` combina decaimiento temporal exponencial + access boost

### `get(node_id: str) -> Node`
Devuelve el `Node` en crudo, con su vector matemático y arrays relacionales puros.

### `get_context(node_id: str, depth: int = 1) -> dict`
Genera un *Mapa Relacional Corto*: Retorna al nodo envuelto junto con la información detallada de sus padres, vecinos e hijos, perfecto para construir Prompt Contexts robustos para Sistemas Expertos.

### `get_mas_relevante(n: int = 5) -> list[dict]`
Retorna los `n` nodos con mayor score de relevancia (combina edad + accesos).

## ⚙️ Operaciones Core

### `export_md(path: str) -> None`
Exporta a Markdown todo el cerebro organizado por capas.

### `stats() -> dict`
Estadísticas del grafo incluyendo:
```python
{
    "total_nodos": 1247,
    "por_tipo": {"MACRO": 8, "MEDIO": 43, "MEMORIA": 1196},
    "decay_rate": 0.01,
    "nodos_muy_relevantes": 42,      # relevancia > 0.5
    "nodos_desatendidos": 8,         # relevancia < 0.1
    "relevancia_promedio": 0.34,
    "threshold_actual": 4,
    "balance_ratio": 0.94,
    "rebalanceo_recomendado": False
}
```

### `save() / load() -> None`
Operación manual si `autosave=False`.
