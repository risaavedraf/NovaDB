# MindReader

Frontend de visualización para NovaDB. Renderiza el Knowledge Graph semántico como un grafo interactivo en el navegador.

## Stack

- **Backend:** FastAPI — REST endpoints que exponen el grafo de NovaDB
- **Frontend:** React + `react-force-graph` — WebGL para renderizado de nodos con física

## Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/graph` | GET | Topología completa: `{nodes, edges}` |
| `/api/node/{id}` | GET | Contexto completo de un nodo |
| `/api/search?q={query}` | GET | Búsqueda semántica, retorna top-K |
| `/api/stats` | GET | Estadísticas del grafo |

## Quick Start

```bash
# Desde la raíz del monorepo
pip install fastapi uvicorn
cd mind-reader
python api.py
```

Abrir `http://localhost:8000` en el navegador.

## Estructura

```
mind-reader/
├── api.py          # FastAPI backend
├── MindReader_PRD.md  # Product Requirements
└── web/            # Frontend (React app)
```
