# MindReader 🧠👁️

Frontend de visualización en 3D para NovaDB. Renderiza el Knowledge Graph semántico completo (las 3 jerarquías: MACRO, MEDIO, MEMORIA) como un grafo de fuerzas interactivo en el navegador.

## Stack Tecnológico

- **Backend:** FastAPI — Endpoints REST que leen directamente el archivo `.msgpack` u otra DB en vivo.
- **Frontend:** Astro + React + `react-force-graph` — Renderizado WebGL de alto desempeño para simular físicas en miles de nodos.

## Endpoints del Backend

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/graph` | GET | Topología completa del cerebro: `{nodes, edges}` |
| `/api/node/{id}` | GET | Contexto mental de un nodo (hijos, padres, vecinos) |
| `/api/search?q={query}` | GET | Búsqueda semántica usando el embedder, retorna top-K |
| `/api/stats` | GET | Estadísticas de uso y salud del motor NovaDB |

## Inicio Rápido (Quick Start)

MindReader requiere levantar en paralelo tanto el puente de datos (FastAPI) como el visualizador web (Astro).

```bash
# Terminal 1 — Backend (Desde la raíz del monorepo)
# Importante: Define la variable de entorno a la DB de producción si es necesario
$env:NOVADB_PATH = 'db/nova_production.msgpack' # (PowerShell)
# export NOVADB_PATH='db/nova_production.msgpack' # (Bash/Zsh)
.\venv\Scripts\python.exe -m uvicorn mind-reader.api:app --port 8000 --reload

# Terminal 2 — Frontend App
cd mind-reader/web
npm install
npm run dev
# → Abre http://localhost:4321 en tu navegador
```

## Estructura

```text
mind-reader/
├── api.py             # FastAPI backend genérico de lectura
├── MindReader_PRD.md  # Product Requirements Document Original
└── web/               # Aplicación Astro + React moderna
    ├── src/
    │   ├── components/ 
    │   │   ├── MindGraph.jsx  # Render WebGL del grafo 3D
    │   │   └── NodePanel.jsx  # HUD de estadísticas
    │   └── pages/
```

