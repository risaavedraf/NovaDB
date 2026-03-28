# NovaDB MCP Server

Servidor MCP (Model Context Protocol) para NovaDB — tu motor de memoria semántica jerárquica universal.

## ¿Qué es esto?

NovaDB MCP convierte tu motor de memoria NovaDB en una herramienta que CUALQUIER agente de IA puede usar:
- **Antigravity**
- **OpenCode**
- **Cursor**
- **Cline**
- **Claude Desktop**
- Cualquier agente compatible con MCP

## Instalación

```bash
# Instalar dependencias
pip install mcp

# O instalar como paquete
cd novadb-mcp
pip install -e .
```

## Configuración

Variables de entorno:

```bash
# Requerido para embeddings y consolidación
GEMINI_API_KEY=tu-api-key

# Opcional
NOVADB_PATH=./nova_production.msgpack  # Ruta del archivo de base de datos
NOVADB_LOG_LEVEL=INFO                  # Nivel de logging (DEBUG/INFO/WARNING)
```

## Uso

### Claude Desktop

Agrega a `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "novadb": {
      "command": "python",
      "args": ["-m", "novadb_mcp.server"],
      "cwd": "<YOUR_PATH>/novadb-mcp",
      "env": {
        "GEMINI_API_KEY": "YOUR_API_KEY_HERE",
        "NOVADB_PATH": "<YOUR_PATH>/nova_production.msgpack"
      }
    }
  }
}
```

### OpenCode

Ver `examples/opencode.json` para configuración.

### Línea de comandos

```bash
# Ejecutar el servidor MCP
python -m novadb_mcp.server
```

## Tools Disponibles

### Memoria

| Tool | Descripción |
|------|-------------|
| `memorizar` | Guarda un recuerdo en la memoria semántica |
| `recordar` | Busca recuerdos por significado |
| `obtener` | Recupera un recuerdo por ID |
| `olvidar` | Elimina un recuerdo (pendiente implementación) |

### Contexto

| Tool | Descripción |
|------|-------------|
| `reflejar` | Obtiene el contexto alrededor de un nodo |
| `actualizar` | Modifica un recuerdo existente |
| `conectar` | Relaciona dos memorias explícitamente |

### Sistema

| Tool | Descripción |
|------|-------------|
| `analizar` | Estadísticas del grafo de memoria |
| `rebalancear` | Reorganiza el grafo automáticamente |

### Admin

| Tool | Descripción |
|------|-------------|
| `guardar` | Persiste el grafo a disco |
| `cargar` | Carga un grafo desde disco |
| `exportar` | Exporta a Markdown legible |

## Ejemplos de Uso

### Guardar un recuerdo
```
Usuario: "Memoriza que mi banda favorita es Deftones"
Agente → memorizar(texto="La banda favorita de r1cky es Deftones", tipo="MEMORIA")
```

### Buscar recuerdos
```
Usuario: "¿Qué bandas me gustan?"
Agente → recordar(consulta="bandas musicales favoritas", cantidad=5)
```

### Ver estadísticas
```
Usuario: "¿Cómo está tu memoria?"
Agente → analizar()
```

## Arquitectura

```
novadb-mcp/
├── src/novadb_mcp/
│   ├── server.py        # FastMCP server
│   ├── config.py        # Configuración (env vars)
│   ├── serializers.py   # Node → JSON
│   └── tools/
│       ├── memoria.py   # memorizar, recordar, obtener
│       ├── contexto.py  # reflejar, actualizar, conectar
│       ├── sistema.py   # analizar, rebalancear
│       └── admin.py     # guardar, cargar, exportar
└── tests/
```

## Dependencias

- `mcp>=1.0.0` — Protocolo MCP
- `novadb` — Motor de memoria (referencia local)

## License

MIT
