# NovaDB 🧠

**Hierarchical Semantic Memory Engine for AI Agents.**

Combines vector search, automatic hierarchy, and simple persistence — in a single monorepo. Connect any AI agent via MCP in minutes.

## Quick Start

### Option A — `uv` (recommended, no venv management needed)

```bash
# Install uv once (Linux / WSL / macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone & run
git clone https://github.com/risaavedraf/NovaDB.git
cd NovaDB

uv sync                   # installs everything automatically
cp .env.example .env      # add your GEMINI_API_KEY (optional)

# Verify
uv run python -c "from novadb.novadb import NovaDB; print('NovaDB OK')"
```

### Option B — `pip` + venv (traditional)

```bash
git clone https://github.com/risaavedraf/NovaDB.git
cd NovaDB

python -m venv venv
source venv/bin/activate        # Linux / WSL / macOS
# or: .\venv\Scripts\activate   # Windows

pip install -e ".[all]"
cp .env.example .env
```

## Connecting to an AI Agent (MCP)

The server automatically loads `.env` from the monorepo root — no need to duplicate keys in the agent config.

**Step 1:** Fill in your `.env`:
```bash
cp .env.example .env
# Set GEMINI_API_KEY and NOVADB_PATH inside
```

**Step 2:** Add to your agent's MCP config (opencode, Antigravity, Claude Desktop, etc.):

**With `uv` (recommended):**
```json
{
  "mcpServers": {
    "novadb": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/novadb", "-m", "novadb_mcp.server"]
    }
  }
}
```

**With venv:**
```json
{
  "mcpServers": {
    "novadb": {
      "command": "/path/to/novadb/venv/bin/python",
      "args": ["-m", "novadb_mcp.server"]
    }
  }
}
```

> **WSL tip:** run `which uv` or `which python` to get the exact path.  
> **Windows tip:** use full absolute path to `venv\Scripts\python.exe`.

## MindReader — 3D Visualization

```bash
# Terminal 1 — Backend
cd mind-reader
uvicorn api:app --port 8000 --reload

# Terminal 2 — Frontend
cd mind-reader/web
npm install
npm run dev
# → Open http://localhost:4321
```

## Monorepo Structure

| Module | Description |
|--------|-------------|
| [`novadb/`](novadb/) | Core — 3-layer semantic memory engine (MACRO / MEDIO / MEMORIA) |
| [`novadb-mcp/`](novadb-mcp/) | MCP Server — 13 tools to connect any AI agent |
| [`mind-reader/`](mind-reader/) | Frontend — Interactive Knowledge Graph visualization |
| [`docs/`](docs/) | Docs — Architecture, MCP tools reference, demo guide |

## Architecture

```
novadb/          → Core engine  (O(√N) search, automatic clustering)
novadb-mcp/      → MCP bridge   (FastMCP → 13 standardized tools)
mind-reader/     → Visualizer   (FastAPI + React + 3D force-graph)
```

The three modules connect: the **core** processes memory, the **MCP server** exposes tools to agents, and **MindReader** renders the live knowledge graph.

## Embedder Modes

| Mode | Model | Dims | Requirement |
|------|-------|------|-------------|
| **Gemini** (default) | `gemini-embedding-001` | 768 | `GEMINI_API_KEY` |
| **Local** (offline) | `all-MiniLM-L6-v2` | 384 | `sentence-transformers` |

The system auto-detects which mode to use. If no API key is set, it falls back to the local model automatically.

> **Note:** A database built with one embedder is **not compatible** with another (different vector dimensions). The system will raise an `IncompatibleEmbedderError` with a clear message if this happens.

## Documentation

- [Architecture](docs/architecture.md) — Full Mermaid system diagram
- [How It Works](docs/how_it_works.md) — Conceptual explanation of the 3 layers
- [MCP Tools](docs/mcp_tools.md) — Reference for all 13 MCP tools
- [Demo Script](docs/demo_script.md) — Presentation guide

## Status

- ✅ Core v1.1 — Temporal decay, hierarchical indices, 126 tests
- ✅ MCP Server — 13 tools, fully documented
- ✅ MindReader — FastAPI backend + React 3D frontend

---

MIT License · Built by **r1cky**
