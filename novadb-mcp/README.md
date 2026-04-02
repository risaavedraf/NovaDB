# NovaDB MCP Server

Servidor MCP (Model Context Protocol) para NovaDB — tu motor de memoria semántica jerárquica universal.

## ¿Qué es esto?

NovaDB MCP convierte tu motor de memoria NovaDB en una herramienta que CUALQUIER agente de IA puede usar para auto-dotarse de una memoria episódica estructurada y perdurable:
- **Antigravity**
- **OpenCode**
- **Cursor**
- **Cline**
- **Claude Desktop**
- Cualquier agente compatible con MCP

## Instalación

```bash
# Se recomienda instalar todo desde la raíz usando uv:
uv sync

# O a la forma tradicional (dentro de un venv):
pip install mcp
cd novadb-mcp
pip install -e .
```

## Configuración y Variables de Entorno

El servidor carga dinámicamente el archivo `.env` desde la raíz de tu monorepo:

```bash
# Requerido para embeddings (si no usas la versión Local)
GEMINI_API_KEY=tu-api-key

# Opcional (Sobrescribir si es necesario)
NOVADB_PATH=./nova_production.msgpack
NOVADB_LOG_LEVEL=INFO
```

## Uso y Configuración Estándar

### OpenCode (y clientes similares basados en Array)
Añadir a la configuración de `opencode`:

```json
{
  "mcp": {
    "novadb": {
      "type": "local",
      "command": [
        "uv",
        "run",
        "--project", "/ruta/absoluta/al/NovaDB",
        "-m", "novadb_mcp.server"
      ]
    }
  }
}
```

### Claude Desktop
Añadir a `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "novadb": {
      "command": "uv",
      "args": [
        "run",
        "--project", "/ruta/absoluta/al/NovaDB",
        "-m", "novadb_mcp.server"
      ]
    }
  }
}
```

## Tools Disponibles (x14)

### 🧠 Memoria

| Tool | Descripción |
|------|-------------|
| `memorizar` | Guarda un recuerdo fragmentado en memoria (Fase 1 del clúster natural). |
| `recordar` | Busca recuerdos instantáneamente usando vectores y O(√N). |
| `obtener` | Recupera el contenido exacto de un nodo con metadata desde su ID. |
| `olvidar` | Elimina un recuerdo ("Lobotomía"), devolviendo sus hijos en forma huérfana. |

### 🕸️ Contexto

| Tool | Descripción |
|------|-------------|
| `reflejar` | Obtiene el entorno mental de un nodo (padres MACRO, hijos, hermanos). |
| `actualizar` | Modifica el texto de un recuerdo (actualizando su vector y reposición). |
| `conectar` | Conecta manualmente 2 memorias que no superaron el umbral de similitud. |

### ⚙️ Sistema y Consolidación

| Tool | Descripción |
|------|-------------|
| `analizar` | Retorna radiografía completa, ratios de saturación y tamaño del cerebro. |
| `consolidar_proponer` | **Fase 1:** Sugiere agrupaciones lógicas de fragmentos huérfanos sin afectar la DB. |
| `consolidar_ejecutar` | **Fase 2:** Ejecuta el nombramiento del nodo MEDIO que amarra a los huérfanos. |
| `rebalancear` | Reorganiza matemáticamente el grafo en base a relevancia y tiempo de vida. |

### 🚨 Admin

| Tool | Descripción |
|------|-------------|
| `guardar` | Fuerza una instantánea a disco. |
| `cargar` | Destruye la memoria en RAM actual cargando una diferente. |
| `exportar` | Exporta la topología a un `.md` legible. |

## Arquitectura

```text
novadb-mcp/
├── src/novadb_mcp/
│   ├── server.py        # Configuración del `FastMCP` server
│   ├── config.py             
│   ├── serializers.py        
│   └── tools/
│       ├── memoria.py   
│       ├── contexto.py  
│       ├── sistema.py   
│       └── admin.py     
```
