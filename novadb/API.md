# NovaDB - Documentación de API Pública

La fachada de la base de datos matemática es la clase `NovaDB`, ubicada en `novadb.py`. Esta es la única clase que deberías instanciar en tu backend.

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
    log_file=None              # None = stdout, o ruta a archivo .log para MCP
)
```

## ✍️ Métodos de Escritura

### `insert(text: str, tipo: str = "MEMORIA", metadata: dict | None = None) -> str`
Inserta un nuevo contenido lógico. NovaDB vectoriza el texto, lo coloca semánticamente en el barrio mental correcto y maneja las consolidaciones jerárquicas en segundo plano.

### `connect(id_a: str, id_b: str, tipo_conexion: str, peso: float = 1.0) -> None`
Añade un puente explícito y forzado entre dos nodos. Útil cuando se quieren cruzar conceptos a pesar de que la matemática no indique una similitud alta.

### `update(node_id: str, fields: dict[str, Any]) -> None`
Reescribe la metainformación o el `text` de un nodo. Si el `text` cambia, el nodo se despega temporalmente y es vectorizado nuevamente para encontrar su nuevo lugar en el espacio latente.

### `olvidar(node_id: str) -> dict`
Borra permanentemente un nodo de la memoria de forma quirúrgica. Si el nodo tenía hijos, estos quedan sueltos como "huérfanos". Retorna el ID de las memorias huérfanas resultantes.

## 🔭 Métodos de Lectura

### `search(query: str, n: int = 5) -> list[dict]`
Entrega los `n` nodos de tipo `MEMORIA` más coherentes con tu query. 
- Usa ruteo interno **O(√N)** con índices jerárquicos saltando por MACROs y MEDIOs.
- Re-rankeo final: `cosine_similarity * 0.7 + relevancia * 0.3`

### `get(node_id: str) -> Node`
Devuelve el objeto `Node` en crudo, con su vector matemático y arrays relacionales. No lo uses en APIs públicas ya que el vector es extremadamente pesado para procesar en JSON.

### `get_context(node_id: str, depth: int = 1) -> dict`
Genera un *Mapa Relacional Corto*: Retorna el nodo envuelto junto con la información detallada de sus padres, vecinos e hijos, perfecto para inyectar *Contexto Mental* a Prompts del Agente.

## ⚙️ Operaciones Core / Sistema

### `consolidar_proponer(umbral: float = 0.82) -> dict`
**Nueva en v1.2**: Explora topológicamente las memorias "huérfanas". Retorna a un Agente listas sugeridas de clústeres a formar, mostrando el texto previo para asistir en el nombramiento. No modifica la base de datos.

### `consolidar_ejecutar(grupos: list[dict]) -> dict`
Genera formalmente los nodos MEDIO pasados por el array de `grupos` (el cual debe contener `"nodo_ids"` y `"nombre"`). Los auto-conecta a su ancla MACRO más similar. Ejecuta guardado (autosave).

### `rebalancear() -> dict`
Operación de mantenimiento profundo. Explora todos los grupos `MEDIO` y distribuye o fusiona memorias huérfanas en diferentes clústeres equilibrando el sistema. 

### `export_md(path: str) -> None`
Exporta a texto plano Markdown todo el cerebro organizado en viñetas por capas.

### `stats() -> dict`
Entrega una radiografía matemática y operativa.
```python
{
    "total_nodos": 1247,
    "por_tipo": {"MACRO": 8, "MEDIO": 43, "MEMORIA": 1196},
    "nodos_huerfanos": 71,
    "nodos_muy_relevantes": 42,
    "relevancia_promedio": 0.34,
    "balance_ratio": 0.94,
    "rebalanceo_recomendado": False
}
```

### `save() / load() -> None`
Operación manual recomendada si configuraste el constructor con `autosave=False`.
