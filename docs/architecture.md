# Arquitectura — NovaDB

## Visión General del Sistema

```mermaid
graph TB
    subgraph "Monorepo NovaDB"
        subgraph "novadb — Motor Core"
            CORE[Motor NovaDB<br/>Jerarquía de 3 capas]
            MEM[Módulo de Memoria<br/>Almacenamiento de Nodos]
            STORE[Capa de Persistencia<br/>JSON / MessagePack]
            EMBED[Interfaz Embedder<br/>API Gemini / Local]
            CORE --> MEM
            CORE --> STORE
            CORE --> EMBED
        end

        subgraph "novadb-mcp — Servidor MCP"
            MCP[Servidor FastMCP]
            TMEM[memorizar / recordar / obtener]
            TCTX[reflejar / actualizar / conectar]
            TSYS[analizar / consolidar / rebalancear]
            TADM[guardar / cargar / exportar]
            MCP --> TMEM
            MCP --> TCTX
            MCP --> TSYS
            MCP --> TADM
        end

        subgraph "mind-reader — Visualización"
            API[Backend FastAPI]
            WEB[Astro + React + force-graph]
            SOCK[API REST / Polling]
            API --> WEB
            API --> SOCK
        end
    end

    subgraph "Externo"
        GEM[API Gemini<br/>Embeddings]
        AGENTS[Agentes IA<br/>OpenCode / Cursor / Claude]
    end

    CORE <--> GEM
    MCP <--> AGENTS
    API <--> CORE
    TMEM --> CORE
```

## Flujo de Datos

```mermaid
sequenceDiagram
    participant Usuario
    participant Agente as Agente IA
    participant MCP as novadb-mcp
    participant DB as novadb Core
    participant Gemini

    Usuario->>Agente: "Recuerda que mi banda favorita es Deftones"
    Agente->>MCP: memorizar(texto, tipo)
    MCP->>Gemini: Generar embedding
    Gemini-->>MCP: Vector [0.23, -0.41, ...]
    MCP->>DB: Almacenar nodo con vector
    DB-->>MCP: Nodo creado (ID: 42)
    MCP-->>Agente: Confirmación
    Agente-->>Usuario: "Entendido, guardado en memoria"

    Usuario->>Agente: "¿Qué bandas me gustan?"
    Agente->>MCP: recordar(consulta="bandas favoritas")
    MCP->>Gemini: Vectorizar consulta
    Gemini-->>MCP: Vector de la consulta
    MCP->>DB: Búsqueda por similitud coseno
    DB-->>MCP: Resultados Top-K
    MCP-->>Agente: Memorias encontradas
    Agente-->>Usuario: "Tu banda favorita es Deftones"
```

## Modelo Jerárquico

```mermaid
graph LR
    M1[MACRO<br/>Arquitecturas Cloud] --> MED1[MEDIO<br/>AWS]
    M1 --> MED2[MEDIO<br/>GCP]
    MED1 --> MEM1[MEMORIA<br/>Lambda caro para procs de 5min]
    MED1 --> MEM2[MEMORIA<br/>S3 costo por GB]
    MED2 --> MEM3[MEMORIA<br/>Cloud Functions barato]
```

## Stack Tecnológico

| Capa | Tecnología | Propósito |
|-------|-----------|---------|
| Core | Python, NumPy, msgpack | Motor semántico + persistencia binaria hiper-rápida |
| Embeddings | API Gemini / Local | Conversión de texto → vector (768 o 384 dimensiones) |
| MCP | FastMCP, Python | Puente de protocolo estándar para dotar de memoria a IA |
| Backend API | FastAPI | Endpoints REST para ingestar el grafo al visualizador |
| Frontend | Astro, React, 3D force-graph | Renderizado del grafo espacial y topológico interactivo |
| Tiempo Real | Polling / JSON Fetch | Actualización en vivo del estado de la memoria |
