# Architecture — NovaDB

## System Overview

```mermaid
graph TB
    subgraph "NovaDB Monorepo"
        subgraph "novadb — Core Engine"
            CORE[NovaDB Engine<br/>3-layer hierarchy]
            MEM[Memory Module<br/>Node storage]
            STORE[Storage Layer<br/>JSON / MessagePack]
            EMBED[Embedder Interface<br/>Gemini API]
            CORE --> MEM
            CORE --> STORE
            CORE --> EMBED
        end

        subgraph "novadb-mcp — MCP Server"
            MCP[FastMCP Server]
            TMEM[memorizar / recordar / obtener]
            TCTX[reflejar / actualizar / conectar]
            TSYS[analizar / rebalancear]
            TADM[guardar / cargar / exportar]
            MCP --> TMEM
            MCP --> TCTX
            MCP --> TSYS
            MCP --> TADM
        end

        subgraph "mind-reader — Visualization"
            API[FastAPI Backend]
            WEB[React + force-graph]
            SOCK[WebSocket / Polling]
            API --> WEB
            API --> SOCK
        end
    end

    subgraph "External"
        GEM[Gemini API<br/>Embeddings]
        AGENTS[AI Agents<br/>OpenCode / Cursor / Claude]
    end

    CORE <--> GEM
    MCP <--> AGENTS
    API <--> CORE
    TMEM --> CORE
```

## Data Flow

```mermaid
sequenceDiagram
    participant User
    participant Agent as AI Agent
    participant MCP as novadb-mcp
    participant DB as novadb Core
    participant Gemini

    User->>Agent: "Remember that my band is Deftones"
    Agent->>MCP: memorizar(texto, tipo)
    MCP->>Gemini: Generate embedding
    Gemini-->>MCP: Vector [0.23, -0.41, ...]
    MCP->>DB: Store node with vector
    DB-->>MCP: Node created (ID: 42)
    MCP-->>Agent: Confirmation
    Agent-->>User: "Got it, stored in memory"

    User->>Agent: "What bands do I like?"
    Agent->>MCP: recordar(consulta="bandas favoritas")
    MCP->>Gemini: Embed query
    Gemini-->>MCP: Query vector
    MCP->>DB: Cosine similarity search
    DB-->>MCP: Top-K results
    MCP-->>Agent: Memories found
    Agent-->>User: "Your favorite band is Deftones"
```

## Hierarchy Model

```mermaid
graph LR
    M1[MACRO<br/>Arquitecturas Cloud] --> MED1[MEDIO<br/>AWS]
    M1 --> MED2[MEDIO<br/>GCP]
    MED1 --> MEM1[MEMORIA<br/>Lambda caro para 5min]
    MED1 --> MEM2[MEMORIA<br/>S3 costo por GB]
    MED2 --> MEM3[MEMORIA<br/>Cloud Functions barato]
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Core | Python, NumPy, msgpack | Semantic engine + persistence |
| Embeddings | Gemini API | Text → vector conversion |
| MCP | FastMCP, Python | Protocol bridge for AI agents |
| Backend API | FastAPI | REST endpoints for visualization |
| Frontend | React, force-graph | Interactive graph rendering |
| Real-time | WebSocket / Polling | Live memory updates |
