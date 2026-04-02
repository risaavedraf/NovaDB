# Referencia de Herramientas MCP

NovaDB expone 14s herramientas a través del Model Context Protocol (MCP). Cualquier agente compatible con MCP puede utilizarlas para dotarse de memoria a largo plazo.

## Módulo `memoria` — Operaciones Base

### `memorizar`
Almacena texto como un nodo generando su embedding vectorial semántico.

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|----------|-------------|
| `texto` | string | Sí | El contenido de la memoria. |
| `tipo` | string | No | `MACRO`, `MEDIO` o `MEMORIA` (por defecto: `MEMORIA`). |
| `metadata` | dict | No | Datos extra en formato clave-valor. |

### `recordar`
Busca memorias por significado semántico (similitud matemática), retornando los nodos más similares a la consulta.

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|----------|-------------|
| `consulta` | string | Sí | El concepto o pregunta que estás buscando. |
| `cantidad` | int | No | Número máximo de resultados (por defecto: 5). |

### `obtener`
Recupera un nodo de memoria específico por su ID exacto.

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|----------|-------------|
| `node_id` | string | Sí | El ID del nodo a recuperar. |

### `olvidar`
Borrado quirúrgico de un nodo. Retorna los IDs de los nodos hijos que quedaron "huérfanos".

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|----------|-------------|
| `node_id` | string | Sí | ID del nodo a borrar definitivamente. |

## Módulo `contexto` — Navegación del Grafo

### `reflejar`
Obtiene el "vecindario" alrededor de un nodo: sus padres (MACROS/MEDIOS), sus hijos (MEMORIAS) y sus vecinos horizontales.

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|----------|-------------|
| `node_id` | string | Sí | ID del nodo central para el reflejo. |
| `profundidad` | int | No | Niveles hacia arriba/abajo (por defecto: 1). |

### `actualizar`
Modifica el contenido o la metadata de un nodo existente. Si se cambia el texto, se regenera el embedding.

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|----------|-------------|
| `node_id` | string | Sí | ID del nodo a editar. |
| `texto` | string | No | Nuevo contenido de texto. |
| `metadata` | dict | No | Metadata a fusionar con la existente. |

### `conectar`
Crea una conexión explícita manual entre dos nodos, forzando una relación gravitacional que la matemática podría no haber captado.

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|----------|-------------|
| `origen_id` | string | Sí | ID del nodo origen. |
| `destino_id` | string | Sí | ID del nodo destino. |
| `tipo_conexion` | string | No | Tipo de relación (ej. "depende_de"). |
| `peso` | float | No | Peso gravitacional de la conexión. |

## Módulo `sistema` — Mantenimiento y Agentic Clustering

### `analizar`
Obtiene estadísticas globales y métricas de salud del inmenso grafo de memoria.

*Sin parámetros.*

### `consolidar_proponer`
**Fase 1:** Analiza vectores y propone agrupaciones lógicas de nodos "huérfanos" que sean muy similares, sin afectar la base de datos real.

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|----------|-------------|
| `umbral` | float | No | Umbral mínimo de similitud coseno (por defecto: 0.82). |

### `consolidar_ejecutar`
**Fase 2:** Ejecuta la creación del nodo MEDIO para organizar un grupo de memorias propuesto. El nodo se auto-conecta a su raíz MACRO más adecuada.

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|----------|-------------|
| `nodo_ids` | list | Sí | Lista de IDs (strings) de los nodos MEMORIA a fusionar en el nuevo grupo. |
| `nombre` | string | Sí | Nombre representativo humano que se le dará al nodo MEDIO organizado. |

### `rebalancear`
Reorganiza forzosamente la jerarquía del grafo.

*Sin parámetros.*

## Módulo `admin` — Persistencia

### `guardar`
Fuerza un guardado o snapshot del grafo en formato MessagePack o JSON al disco.

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|----------|-------------|
| `ruta` | string | No | Ruta del archivo a guardar (por defecto usa la ruta configurada en el servidor). |

### `cargar`
Carga un grafo de memoria específico desde el disco, destruyendo el entorno en memoria actual.

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|----------|-------------|
| `ruta` | string | No | Ruta del archivo a cargar. |

### `exportar`
Exporta una instantánea (snapshot) de toda tu "mente" a un documento Markdown legible para humanos.

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|----------|-------------|
| `ruta` | string | Sí | Ruta del archivo `.md` de salida. |