# NovaDB 🧠

**Motor de Memoria Semántica Jerárquica para Agentes de IA.**

NovaDB combina búsqueda vectorial, jerarquía automática y persistencia simple en un único monorepo. Conecta cualquier agente de IA a través de MCP (Model Context Protocol) en cuestión de minutos y dótalo de una memoria estructurada a largo plazo.

## Inicio Rápido

### Opción A — `uv` (Recomendado, no requiere manejo manual de venv)

```bash
# Instala uv una vez (Linux / WSL / macOS / Windows)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clona y ejecuta
git clone https://github.com/risaavedraf/NovaDB.git
cd novadb

uv sync                   # Instala todo automáticamente
cp .env.example .env      # Añade tu GEMINI_API_KEY (opcional)

# Verificar instalación
uv run python -c "from novadb.novadb import NovaDB; print('NovaDB OK')"
```

### Opción B — `pip` + venv (Tradicional)

```bash
git clone https://github.com/risaavedraf/NovaDB.git
cd novadb

python -m venv venv
source venv/bin/activate        # Linux / WSL / macOS
# o en Windows: .\venv\Scripts\activate

pip install -e ".[all]"
cp .env.example .env
```

## Conectando a un Agente de IA (MCP)

NovaDB soporta los formatos principales de configuración de MCP. El servidor carga automáticamente el archivo `.env` desde la raíz del monorepo, por lo que no necesitas duplicar tus claves API en la configuración del agente.

### 1. Formato OpenCode.ai (Basado en Arreglos)
OpenCode utiliza un esquema único. Requiere `"type": "local"` y un **arreglo (array)** para el comando. No utiliza el campo `args`.

**Edita tu `opencode.json`:**
```json
{
  "mcp": {
    "novadb": {
      "type": "local",
      "command": [
        "uv", 
        "run", 
        "--project", "/ruta/absoluta/a/NovaDB", 
        "-m", "novadb_mcp.server"
      ]
    }
  }
}
```

### 2. Formato Estándar MCP (Claude Desktop, Antigravity, etc.)
Utilizado por la mayoría de clientes estándar. Usa `"mcpServers"`, un comando en formato string, y un arreglo `args`.

**Edita tu `mcp_config.json` (o equivalente):**
```json
{
  "mcpServers": {
    "novadb": {
      "command": "uv",
      "args": [
        "run", 
        "--project", "/ruta/absoluta/a/NovaDB", 
        "-m", "novadb_mcp.server"
      ]
    }
  }
}
```

---

> **Tip para WSL:** ejecuta `which uv` o `which python` para obtener la ruta exacta.
> **Tip para Windows:** utiliza la ruta absoluta completa hacia `venv\Scripts\python.exe` y usa barras normales `/` o dobles barras invertidas `\\`.

## MindReader — Visualizador 3D

MindReader te permite ver la topología de la memoria en tiempo real, observando cómo los nodos MACRO, MEDIO y MEMORIA interactúan y se agrupan.

```bash
# Terminal 1 — Backend (Provee acceso a la base de datos)
$env:NOVADB_PATH = 'db/nova_production.msgpack' # En PowerShell (opcional)
.\venv\Scripts\python.exe -m uvicorn mind-reader.api:app --port 8000 --reload

# Terminal 2 — Frontend (Interfaz 3D Web)
cd mind-reader/web
npm install
npm run dev
# → Abre http://localhost:4321 en tu navegador
```

## Estructura del Monorepo

| Módulo | Descripción |
|--------|-------------|
| [`novadb/`](novadb/) | Motor Core — Memoria semántica de 3 capas (MACRO / MEDIO / MEMORIA) |
| [`novadb-mcp/`](novadb-mcp/) | Servidor MCP — Herramientas estandarizadas para conectar cualquier agente de IA |
| [`mind-reader/`](mind-reader/) | Frontend/Backend — Visualización interactiva del Grafo de Conocimiento en 3D |
| [`docs/`](docs/) | Documentación — Arquitectura, referencia de herramientas MCP, guía de demostración |

## Arquitectura y Consolidación Agentic

El sistema organiza la información en tres niveles jerárquicos:
1. **MEMORIA:** Fragmentos de conocimiento puro ingresados al sistema.
2. **MEDIO:** Clústeres o conceptos formados por la unión natural de múltiples Memorias.
3. **MACRO:** El contexto global u origen fundamental (ej. un Proyecto o una Persona).

**Consolidación en 2 Fases (Nuevo):**
Para mantener un orden lógico y delegar el poder de raciocinio al Agente de IA, NovaDB utiliza un proceso orgánico:
- **`consolidar_proponer`**: El motor analiza la distancia semántica (vectores) y sugiere, sin modificar la base de datos, agrupar memorias huérfanas muy similares (umbral > 0.82).
- **`consolidar_ejecutar`**: El agente recibe la propuesta, decide un título descriptivo y formaliza la creación del nodo MEDIO, el cual se auto-conecta a su MACRO más cercano para mantener la integridad del árbol de memoria.

## Modelos de Embedding

| Modo | Modelo | Dimensiones | Requisito |
|------|-------|------|-------------|
| **Gemini** (por defecto) | `text-embedding-004` / `001` | 768 / 3072 | `GEMINI_API_KEY` |
| **Local** (offline) | `all-MiniLM-L6-v2` | 384 | `sentence-transformers` |

El sistema auto-detecta qué modo utilizar. Si no se configura una clave API en el `.env`, el sistema utiliza silenciosamente el modelo local.

> **Nota Crítica:** Una base de datos construida con un embedder **no es compatible** con otro (debido a las diferentes dimensiones de los vectores matemáticos). El motor verificará esto automáticamente al cargar y lanzará un `IncompatibleEmbedderError` previniendo corrupciones en los datos.

## Estado del Proyecto

- ✅ **Core v1.2** — Clustering semántico en 2 Fases, validación de embeddings, decaimiento temporal y búsqueda O(√N).
- ✅ **Servidor MCP** — Infraestructura de herramientas integradas y probadas bajo OpenCode y entornos nativos.
- ✅ **MindReader** — Visor estable de grafo de fuerzas en 3D (Astro + React + FastAPI).

---

Licencia MIT · Creado por **r1cky** & asistido por **Alma Nova** 🌌

