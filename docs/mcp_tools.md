# MCP Tools Reference

NovaDB exposes 12 tools via the Model Context Protocol (MCP). Any MCP-compatible agent can use them.

## Module `memoria` — Base Operations

### `memorizar`
Store text as a node with semantic vector embedding.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `texto` | string | Yes | The memory content |
| `tipo` | string | No | `MACRO`, `MEDIO`, or `MEMORIA` (default: `MEMORIA`) |
| `metadata` | dict | No | Extra key-value data |

### `recordar`
Search memories by semantic meaning, returns most similar nodes.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `consulta` | string | Yes | What you're looking for |
| `cantidad` | int | No | Max results (default: 5) |

### `obtener`
Retrieve a specific memory by exact ID.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node_id` | string | Yes | Node ID to retrieve |

### `olvidar`
Surgically delete a node, returns orphaned node IDs.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node_id` | string | Yes | Node ID to delete |

## Module `contexto` — Navigation

### `reflejar`
Get the neighborhood around a node: parents, children, and neighbors.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node_id` | string | Yes | Node ID to reflect on |
| `profundidad` | int | No | How many levels up/down (default: 1) |

### `actualizar`
Edit an existing node's content or metadata.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node_id` | string | Yes | Node ID to update |
| `texto` | string | No | New text content |
| `metadata` | dict | No | Metadata to merge |

### `conectar`
Create an explicit connection between two nodes.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `origen_id` | string | Yes | Source node ID |
| `destino_id` | string | Yes | Target node ID |
| `tipo_conexion` | string | No | Relationship type |
| `peso` | float | No | Connection weight |

## Module `sistema` — Maintenance

### `analizar`
Full graph statistics and health metrics.

*No parameters.*

### `consolidar`
Group orphan nodes into MEDIO categories.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `umbral` | float | No | Similarity threshold (default: 0.70) |

### `rebalancear`
Reorganize the graph hierarchy.

*No parameters.*

## Module `admin` — Persistence

### `guardar`
Persist graph to msgpack on disk.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ruta` | string | No | File path (default: configured path) |

### `cargar`
Load graph from disk.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ruta` | string | No | File path to load (default: configured path) |

### `exportar`
Export snapshot to human-readable Markdown.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ruta` | string | Yes | Output file path |