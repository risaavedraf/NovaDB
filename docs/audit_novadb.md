# 🔬 Auditoría de Código — NovaDB v1.1.0

**Fecha**: 2026-04-02  
**Auditor**: Nova  
**Alcance**: Todo el código fuente del monorepo (`novadb/`, `novadb-mcp/`, `mind-reader/`, `scripts/`, config)

---

## Resumen Ejecutivo

| Métrica | Valor |
|---|---|
| Archivos de código auditados | 22 |
| Líneas de código (aprox.) | ~2,500 |
| Hallazgos **CRÍTICO** 🔴 | 5 |
| Hallazgos **MEDIO** 🟡 | 8 |
| Hallazgos **MENOR** 🟢 | 6 |
| Hallazgos **ESTILO** ⚪ | 4 |

**Veredicto General**: El código es funcional, bien estructurado y muestra un diseño sólido con separación clara de responsabilidades. Los hallazgos críticos no son "bugs que rompen todo" sino **vulnerabilidades estructurales** que, de no abordarse, podrían generar problemas en producción o cuando el grafo escale.

---

## Tabla de Hallazgos

| # | Severidad | Componente | Archivo | Descripción |
|---|---|---|---|---|
| C1 | 🔴 CRÍTICO | Core | `graph.py` | `get_node()` tiene efecto colateral en lectura (muta relevancia) |
| C2 | 🔴 CRÍTICO | MindReader | `api.py` | API key hardcodeada en código fuente |
| C3 | 🔴 CRÍTICO | Core | `embedder.py` | `GeminiEmbedder` no reporta `dims` — validación de dimensiones bypaseada |
| C4 | 🔴 CRÍTICO | Core | `graph.py` | Listas `vecinos[]` crecen sin límite (no se aplica `k_vecinos` cap en inserción bidireccional) |
| C5 | 🔴 CRÍTICO | MCP | `server.py` | `sys.path.insert` hardcodeado — frágil en despliegue |
| M1 | 🟡 MEDIO  | Core | `novadb.py` | `connect()` es unidireccional silenciosamente |
| M2 | 🟡 MEDIO  | Core | `search.py` | Doble boost de relevancia en resultados de búsqueda |
| M3 | 🟡 MEDIO  | Core | `consolidator.py` | `verificar_y_consolidar` escanea TODOS los nodos en cada insert — O(N) |
| M4 | 🟡 MEDIO  | Storage | `disk.py` | Escritura no atómica — corrupción posible en crash |
| M5 | 🟡 MEDIO  | MindReader | `api.py` | `db.get()` en loop del API muta el grafo en cada request |
| M6 | 🟡 MEDIO  | Core | `logging_config.py` | `setup_logging` agrega handlers duplicados por cada instancia de NovaDB |
| M7 | 🟡 MEDIO  | Core | `rebalancer.py` | `rebalancear()` llama `necesita_rebalanceo()` internamente — doble check |
| M8 | 🟡 MEDIO  | MCP | `config.py` | Ruta `.env` calculada con 5 `.parent` — rompe si se mueve el package |
| E1 | 🟢 MENOR  | Core | `node.py` | `datetime.now()` sin timezone — ambiguo entre máquinas |
| E2 | 🟢 MENOR  | Core | `graph.py` | `indice_macro` duplica nodo ID como key → node como value (ya está en `nodes`) |
| E3 | 🟢 MENOR  | Storage | `exporter.py` | `getattr(n, 'padres', [])` innecesario — todo Node tiene `padres` |
| E4 | 🟢 MENOR  | MCP | `tools/*.py` | `sys.path.insert` repetido en 4 archivos |
| E5 | 🟢 MENOR  | Core | `consolidator.py` | `_STOPWORDS` hardcodeadas — mantenimiento frágil |
| E6 | 🟢 MENOR  | Project | `pyproject.toml` | No hay `[project.urls]` — sin links a repo/docs |
| S1 | ⚪ ESTILO | Core | `graph.py` | f-strings en `logger.debug()` — evaluación innecesaria |
| S2 | ⚪ ESTILO | Core | `novadb.py` | Mezcla español/inglés en nombres de métodos |
| S3 | ⚪ ESTILO | MCP | varios | Docstrings en español en módulos MCP, inglés en core |
| S4 | ⚪ ESTILO | Core | `node.py` | `to_dict()` serializa `vector` pero `from_dict()` asume float32 |

---

## Análisis Detallado

### 🔴 C1 — `get_node()` muta estado en lectura

**Archivo**: [graph.py](file:///e:/Proyectos/NovaDB/novadb/core/graph.py#L276-L281)

```python
def get_node(self, node_id: str) -> Optional[Node]:
    """Retrieves a node by exact UUID and updates its access count and relevancia."""
    nodo = self.nodes.get(node_id)
    if nodo:
        self.update_relevancia_on_access(nodo)  # ← PROBLEMA
    return nodo
```

**Problema**: Cada vez que alguien lee un nodo (incluyendo operaciones internas como `update()`, `connect()`, `get_context()`), se incrementa `accesos` y se modifica `relevancia`. Esto significa que:
- `connect()` infla la relevancia del nodo de forma artificial
- `update()` llama `self.get(node_id)` que boost relevancia ANTES del update
- `get_context()` boost el nodo central + todos sus padres/vecinos/hijos solo por inspeccionar el contexto
- El MindReader API boost cada nodo del grafo al renderizar el visualizador

**Impacto**: El sistema de relevancia queda polluted, los nodos más "vistos" internamente no son necesariamente los más relevantes *para el usuario*.

**Solución**: Separar en `get_node()` (lectura pura) y `access_node()` (lectura + boost). Solo boostar en `search()`.

---

### 🔴 C2 — API Key hardcodeada

**Archivo**: [api.py](file:///e:/Proyectos/NovaDB/mind-reader/api.py#L22)

```python
API_KEY = os.getenv("MINDREADER_SECRET", "nova-secret-key-2026")
```

**Problema**: Si la variable de entorno no está seteada, el API queda "protegido" con un secret literal en el código fuente. Cualquiera que lea el repo puede acceder.

**Impacto**: Bajo en desarrollo local, pero es un anti-patrón que un profe podría señalar como mala práctica de seguridad.

**Solución**: Eliminar el default. Si no hay key, que el API falle con error claro en vez de funcionar inseguro.

---

### 🔴 C3 — `GeminiEmbedder` no reporta `dims`

**Archivo**: [embedder.py](file:///e:/Proyectos/NovaDB/novadb/core/embedder.py#L58-L96)

```python
class GeminiEmbedder(BaseEmbedder):
    # ...
    # ← NO tiene @property dims
```

**Problema**: `BaseEmbedder.dims` retorna `None`. `GeminiEmbedder` nunca lo override. Esto significa que `_validate_embedder_dims()` en `novadb.py` hace shortcircuit:

```python
if current_dims is None:
    return  # Embedder doesn't report dims (custom) — skip
```

La validación de dimensiones **nunca se ejecuta** cuando se usa Gemini. Si alguien carga una DB hecha con `LocalEmbedder` (384 dims) usando `GeminiEmbedder` (768 dims), *no habrá error* — solo resultados basura silenciosos.

**Solución**: Agregar `dims = 768` al `GeminiEmbedder`.

---

### 🔴 C4 — Vecinos sin cap bidireccional

**Archivo**: [graph.py](file:///e:/Proyectos/NovaDB/novadb/core/graph.py#L262-L266)

```python
for vec_id, _ in top_vecinos:
    node.vecinos.append(vec_id)
    vecino_node = self.nodes[vec_id]
    if node.id not in vecino_node.vecinos:
        vecino_node.vecinos.append(node.id)  # ← Sin limit check
```

**Problema**: Cuando el nodo A se inserta, se eligen sus `k_vecinos` mejores. Pero al escribir la conexión bidireccional, el nodo B puede terminar con más de `k_vecinos` conexiones. Con muchas inserciones, los nodos centrales (semánticamente populares) acumulan decenas de vecinos.

**Impacto**: 
- Los nodos hub inflan el grafo en memoria
- La búsqueda jerárquica expande la frontera con `nodo.vecinos`, haciendo que los hubs contaminen los resultados con candidatos irrelevantes
- Degradación O(N) progresiva en la búsqueda "O(√N)"

**Solución**: Al agregar la conexión inversa, verificar si `len(vecino_node.vecinos) >= k_vecinos` y si es así, descartar el vecino más débil.

---

### 🔴 C5 — `sys.path.insert` hardcodeado en MCP

**Archivo**: [server.py](file:///e:/Proyectos/NovaDB/novadb-mcp/src/novadb_mcp/server.py#L12-L13) y [memoria.py](file:///e:/Proyectos/NovaDB/novadb-mcp/src/novadb_mcp/tools/memoria.py#L11), [contexto.py](file:///e:/Proyectos/NovaDB/novadb-mcp/src/novadb_mcp/tools/contexto.py#L9), [sistema.py](file:///e:/Proyectos/NovaDB/novadb-mcp/src/novadb_mcp/tools/sistema.py#L9), [admin.py](file:///e:/Proyectos/NovaDB/novadb-mcp/src/novadb_mcp/tools/admin.py#L9)

```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
```

**Problema**: Cada módulo MCP manipula `sys.path` directamente para poder importar `novadb`. Esto es frágil, no-portable y se rompe si la estructura de directorios cambia. Además, los 5 archivos repiten la misma línea.

**Solución**: Usar la configuración de workspace de `pyproject.toml` correctamente. NovaDB ya tiene `[tool.uv.workspace]` definido. Si se instala con `pip install -e .` desde la raíz, `novadb` queda disponible sin `sys.path` hacks.

---

### 🟡 M1 — `connect()` es silenciosamente unidireccional

**Archivo**: [novadb.py](file:///e:/Proyectos/NovaDB/novadb/novadb.py#L151-L164)

```python
def connect(self, id_a: str, id_b: str, tipo_conexion: str, peso: float = 1.0) -> None:
    # ...
    nodo_a.conexiones.append({
        "target": id_b,
        "tipo": tipo_conexion,
        "peso": peso
    })
    # ← Nodo B no sabe que A lo conectó
```

**Problema**: La conexión solo se agrega a `nodo_a.conexiones`. El nodo B no tiene referencias inversas. Cuando se busca el contexto de B, la conexión con A no aparece.

**Solución**: Documentar explícitamente que es unidireccional, o agregar opción `bidireccional=True`.

---

### 🟡 M2 — Doble boost de relevancia en búsqueda

**Archivo**: [search.py](file:///e:/Proyectos/NovaDB/novadb/core/search.py#L80-L91)

```python
for nodo in candidatos_finales:
    sim = similitud_coseno(query_vector, nodo.vector)
    combined = self.graph.calculate_combined_score(sim, nodo)  # ← Usa nodo.relevancia en score
    resultados.append((nodo, combined, sim))

resultados.sort(key=lambda x: x[1], reverse=True)
top_results = [(n, comb) for n, comb, sim in resultados[:top_k]]

for nodo, _ in top_results:
    self.graph.update_relevancia_on_access(nodo)  # ← Boost DESPUÉS del ranking
```

**Problema**: El ranking ya incorpora `relevancia` en el score combinado. Y luego boost la relevancia. Esto crea un loop de retroalimentación positiva: nodos que ya eran relevantes se vuelven MÁS relevantes en cada búsqueda, aplastando nodos nuevos. Es un efecto "rich get richer".

**Impacto**: Con el tiempo, los primeros nodos insertados dominan los resultados aunque nodos nuevos sean más semánticamente relevantes.

**Solución no trivial** — es un trade-off de diseño. Opciones:
1. Reducir el `access_boost` a compensar
2. Normalizar `relevancia` periódicamente con decay global
3. Aplicar el boost ANTES del ranking (decisión explícita)

---

### 🟡 M3 — Consolidación O(N) en cada insert

**Archivo**: [consolidator.py](file:///e:/Proyectos/NovaDB/novadb/core/consolidator.py#L67-L93)

```python
def verificar_y_consolidar(self, nuevo_nodo: Node) -> Optional[Node]:
    # ...
    huerfanos = []
    for n in self.graph.nodes.values():  # ← Recorre TODOS los nodos
        if n.tipo == "MEMORIA" and n.id != nuevo_nodo.id:
            padres_medio = [p_id for p_id in n.padres if ...]
            if not padres_medio:
                huerfanos.append(n)
```

**Problema**: Cada vez que se inserta una MEMORIA, se escanean *todos* los nodos del grafo para encontrar huérfanos. Con 100 nodos no se nota. Con 10,000, esto es un bottleneck serio.

**Solución**: Mantener un set `_orphan_ids` que se actualice incrementalmente en insert/delete, en vez de recalcular cada vez.

---

### 🟡 M4 — Escritura no atómica a disco

**Archivo**: [disk.py](file:///e:/Proyectos/NovaDB/novadb/storage/disk.py#L59-L81)

```python
def save_to_msgpack(graph, path, ...):
    # ...
    with open(path, "wb") as f:
        packed = msgpack.packb(data, use_bin_type=True)
        f.write(packed)
```

**Problema**: Si el proceso se mata durante la escritura (crash, Ctrl+C, fallo de corriente), el archivo queda corrupto. No hay backup ni escritura atómica.

**Solución**: Escribir a un archivo temporal (`path + ".tmp"`) y luego hacer un `os.rename()` atómico. Esto es una operación atómica a nivel de filesystem.

---

### 🟡 M5 — MindReader muta el grafo al renderizar

**Archivo**: [api.py](file:///e:/Proyectos/NovaDB/mind-reader/api.py#L74-L87)

```python
for h_id in n.hijos:
    h_node = db.get(h_id)  # ← Llama a NovaDB.get() que llama graph.get_node()
```

**Problema**: Combinado con C1, cada vez que el visualizador carga el grafo, llama `db.get()` por cada hijo y vecino. Esto muta `accesos` y `relevancia` de *todos* los nodos visibles. Un simple F5 en el dashboard infla la relevancia del grafo completo.

**Solución**: Usar `db.graph.nodes.get(h_id)` directamente (acceso sin side-effects), o resolver C1 primero.

---

### 🟡 M6 — Handler logging duplicados

**Archivo**: [logging_config.py](file:///e:/Proyectos/NovaDB/novadb/core/logging_config.py#L5-L24)

```python
def setup_logging(level, log_file):
    # ...
    logger = logging.getLogger('novadb')
    logger.addHandler(console)  # ← Se agrega CADA VEZ que se llama
```

**Problema**: Si se crea más de una instancia de `NovaDB` (o se llama `setup_logging` de nuevo), se agregan handlers duplicados. Cada mensaje de log se imprime N veces.

**Solución**: Verificar si el logger ya tiene handlers antes de agregar.

---

### 🟡 M7 — Doble check de rebalanceo

**Archivo**: [rebalancer.py](file:///e:/Proyectos/NovaDB/novadb/core/rebalancer.py#L38-L44)

```python
def rebalancear(self):
    if not self.necesita_rebalanceo():  # ← Guard clause interna
        return {"fusionados": 0, "redistribuidos": 0}
```

Pero en [novadb.py](file:///e:/Proyectos/NovaDB/novadb/novadb.py#L356-L362):

```python
def _check_auto_rebalance(self):
    if self.rebalancer.necesita_rebalanceo():  # ← Ya lo chequea
        self.rebalancear()  # ← Que internamente chequea DE NUEVO
```

**Problema**: `necesita_rebalanceo()` calcula balance metrics. Se ejecuta dos veces innecesariamente en flujo automático. No es un bug, pero es trabajo duplicado.

---

### 🟡 M8 — Ruta `.env` con 5 niveles de parent

**Archivo**: [config.py](file:///e:/Proyectos/NovaDB/novadb-mcp/src/novadb_mcp/config.py#L16-L17)

```python
_monorepo_root = Path(__file__).parent.parent.parent.parent.parent
```

**Problema**: Si la estructura del monorepo cambia (un directorio más o menos), esta ruta se rompe silenciosamente y no carga las variables de entorno.

---

### 🟢 E1 — `datetime.now()` sin timezone

**Archivo**: [node.py](file:///e:/Proyectos/NovaDB/novadb/core/node.py#L27-L28)

```python
created_at: datetime = field(default_factory=datetime.now)
updated_at: datetime = field(default_factory=datetime.now)
```

**Problema**: `datetime.now()` retorna un datetime "naive" (sin timezone). Si el grafo se comparte entre máquinas en distintas zonas horarias, el decay temporal se calcula mal.

**Solución**: Usar `datetime.now(timezone.utc)` o `datetime.utcnow()`.

---

### 🟢 E3 — `getattr` innecesario en exporter

**Archivo**: [exporter.py](file:///e:/Proyectos/NovaDB/novadb/storage/exporter.py#L29-L30)

```python
medios_libres = [n for n in graph.nodes.values() if n.tipo == "MEDIO" and not getattr(n, 'padres', [])]
```

**Problema**: Todo `Node` tiene `padres` como campo obligatorio del dataclass. El `getattr` con default es código defensivo innecesario que sugiere que hubo un bug anterior de nodos sin `padres`.

---

## ✅ Aspectos Positivos

Porque no todo son bugs — hay cosas que están bien hechas:

1. **Arquitectura modular limpia**: La separación `core/ → storage/ → novadb.py → mcp/` es textbook. Cada capa tiene responsabilidad clara.

2. **Fallback de embedder**: `GeminiEmbedder` → `LocalEmbedder` es elegante. El sistema funciona offline sin configuración.

3. **Consolidación de 2 fases**: El sistema `proponer()` → `ejecutar_grupos()` es un diseño inteligente que permite supervisión humana/agente antes de modificar el grafo.

4. **MCP logging to file**: El manejo de stdio en el servidor MCP (redirigir todo a archivo) demuestra conocimiento del protocolo y previene corrupción del stream.

5. **Validación de dimensiones** (parcial): El concepto de `_validate_embedder_dims()` es correcto — solo falta la implementación completa en GeminiEmbedder.

6. **Suite de tests sólida**: 14 archivos de test cubriendo core, persistence, decay, edge cases, rebalancer, search, update, consolidation, e2e.

7. **Backup rotativo**: `backup.py` con rotación es simple pero funcional.

8. **Diseño del nodo**: El dataclass `Node` es limpio, tiene serialización/deserialización, y los campos están bien elegidos.

---

## Prioridades de Corrección Sugeridas

### Para la presentación (crítico, rápido de arreglar):
1. **C3** — Agregar `dims = 768` al GeminiEmbedder (1 línea)
2. **C2** — Quitar el default de la API key (1 línea)
3. **M6** — Fix logging duplicado (3 líneas)

### Para robustez del sistema (post-presentación):
4. **C1** — Separar `get_node` de access tracking
5. **C4** — Cap bidireccional de vecinos
6. **M4** — Escritura atómica a disco
7. **M3** — Cache incremental de huérfanos

### Para limpieza de código (mejora continua):
8. **C5/E4** — Eliminar `sys.path.insert` con instalación correcta del package
9. **S1-S4** — Consistencia de idioma y estilo
