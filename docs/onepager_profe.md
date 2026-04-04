# NovaDB — Propuesta de Proyecto
**Estudiante:** r1cky  
**Carrera:** Ingeniería en Informática — Especialidad IA  
**Fecha:** Abril 2026

---

## El Problema

Los agentes de inteligencia artificial modernos tienen un problema fundamental: **no tienen memoria real**.

Cuando le hablas a un agente hoy, recuerda lo que dijiste hace 5 minutos pero no lo que dijiste hace 5 días. Cada conversación empieza desde cero. Para proyectos largos, asistentes empresariales o sistemas con múltiples agentes colaborando, esto es un bloqueo crítico.

Las soluciones existentes comprimen el historial en resúmenes que pierden detalle con el tiempo, o guardan hechos aislados sin entender cómo se relacionan entre sí.

---

## La Solución

### NovaDB — Motor de Memoria Semántica para Agentes de IA

Un sistema diseñado desde cero para que los agentes de IA construyan, organicen y consulten su propio conocimiento. Combina en un solo motor lo que normalmente requiere tres tecnologías separadas:

- **Almacenamiento jerárquico** — organiza el conocimiento en niveles de abstracción (MACRO → MEDIO → MEMORIA)
- **Búsqueda semántica O(√N)** — encuentra por *significado*, no por palabras exactas, navegando la jerarquía en lugar de recorrer todo el grafo
- **Integración MCP nativa** — 14 herramientas expuestas vía Model Context Protocol, permitiendo que cualquier agente compatible (Claude, Gemini, GPT) use NovaDB como su memoria sin código de integración

La diferencia clave: los sistemas actuales guardan *hechos*. NovaDB guarda *conocimiento* — con las conexiones entre conceptos que hacen que el conocimiento sea útil.

---

## Por Qué es Distinto

| Característica | Soluciones actuales | NovaDB |
|---|---|---|
| Memoria entre sesiones | Resúmenes que se degradan | Grafo jerárquico que crece y se organiza |
| Búsqueda | Lineal sobre todos los datos | Jerárquica O(√N), navega por concepto |
| Organización | Manual o plana | Automática en 3 niveles (MACRO/MEDIO/MEMORIA) |
| Consolidación | Automática sin supervisión | Interactiva en 2 fases (Proponer → Ejecutar) |
| Integración | SDK propietario o REST | MCP nativo — estándar abierto de la industria |
| Auditabilidad | Sin trail de operaciones | Cada operación queda registrada y es reversible |

---

## Impacto Real: Escala, Ahorro y Descubrimiento

### El problema de escala que nadie resuelve

Las soluciones actuales funcionan con 50 memorias. Con 10,000, colapsan. NovaDB es una **base de datos**, no un buffer — está diseñado para crecer sin degradar.

| Volumen | RAG plano (ChromaDB/Mem0) | NovaDB |
|---|---|---|
| 100 memorias | Funciona bien | Funciona bien |
| 1,000 memorias | Ruido creciente, recall baja | Jerarquía filtra, calidad estable |
| 10,000 memorias | Degradación severa, costoso | **O(√N) sostenido, consolidación mantiene orden** |

### Ahorro en tokens por query

El token es la moneda de los LLMs. Cada token inyectado en contexto es dinero y tiempo. NovaDB inyecta solo lo relevante navegando la jerarquía, en vez de volcar todo o buscar en lista plana.

| Volumen | Tokens/query (RAG plano) | Tokens/query (NovaDB) | Ahorro | Ahorro mensual (Sonnet) |
|---|---|---|---|---|
| 100 memorias | 1,500 | 750 | **50%** | ~$1 |
| 1,000 memorias | 1,500 | 750 | **50%** | ~$4 |
| 10,000 memorias | 2,000+ (ruido) | 750 | **60-70%** | ~$14-34 |

*(Asumiendo 20 queries/día. GPT-4o: $2.50/1M input tokens. Claude Sonnet: $3/1M input tokens.)*

### Pero lo que importa no es cuántos tokens — es cuán relevantes son

La mayoría de sistemas compiten por quién inyecta menos tokens. NovaDB compite por quién inyecta los tokens **más relevantes**.

```
Relevancia del contexto = (contexto realmente útil) / (contexto total inyectado)
```

| Sistema | Relevancia del contexto inyectado | Qué pasa con el agente |
|---|---|---|
| Full-context (dump completo) | ~30-50% | Mucho ruido, pierde el foco |
| Mem0 / Letta / Cognee | ~60-75% | Buen ahorro de tokens, pero ruido residual |
| **NovaDB** (jerarquía + consolidación) | **~70-90%** | Contexto denso y limpio |

Resultado: el agente recibe contexto más denso y limpio → razona mejor, alucina menos y mantiene coherencia incluso cuando la memoria crece a miles de nodos.

### Búsqueda semántica: conexiones que no esperabas

Aquí está la diferencia fundamental. NovaDB no es un diccionario que busca por palabra clave — es un grafo semántico que busca por **significado**. Cuando el agente busca "costos de Lambda", NovaDB no solo encuentra memorias que mencionan "Lambda" — encuentra memorias sobre *optimización de costos serverless*, *problemas de timeout en funciones*, o *arquitectura event-driven* porque semánticamente están en el mismo espacio vectorial.

Esto es lo que convierte a NovaDB en una base de datos de conocimiento y no un simple almacén:

- **Búsqueda por concepto, no por palabra**: "¿qué pasó con el deploy?" encuentra memorias sobre "CI/CD falló", "Docker no arrancaba", "GitHub Actions timeout" — sin que ninguna diga exactamente "deploy".
- **Descubrimiento de patrones**: al insertar una memoria nueva, el grafo la conecta automáticamente con memorias semánticamente similares. El agente descubre relaciones que no buscaba activamente.
- **Relevancia adaptativa**: los nodos más útiles suben en relevancia por uso real, los irrelevantes decaen temporalmente. El grafo se organiza solo.

### Comparación con soluciones existentes

| Sistema | Qué es | Memoria | Búsqueda | Consolidación | Escala |
|---|---|---|---|---|---|
| **LangChain Memory** | Buffer de contexto | Resumen que degrada | Ninguna | No | ❌ Se pierde |
| **Mem0** | Memoria key-value | Hechos aislados planos | Vectorial lineal | Automática (sin supervisión) | ⚠️ Cloud dependiente |
| **Letta (MemGPT)** | Memoria paginada | Bloques con paging | Lineal + paging | No | ⚠️ Requiere PostgreSQL |
| **Cognee** | Grafo de conocimiento | Nodos y relaciones | Vectorial + grafo | Automática | ⚠️ Requiere Neo4j |
| **NovaDB** | **Motor de memoria jerárquica** | **Grafo jerárquico (3 niveles)** | **Jerárquica O(√N)** | **2 fases supervisadas** | **✅ 1 archivo local** |

**Lo que diferencia a NovaDB:**
1. **Es una base de datos, no un buffer** — diseñado para 10K+ nodos sin degradar
2. **La búsqueda encuentra conexiones inesperadas** — por significado, no por palabras
3. **La consolidación es supervisada** — el agente decide, no una caja negra
4. **Cero infraestructura** — un solo archivo `.msgpack`, funciona offline

---

## Casos de Uso Concretos

**Agente de coding en proyecto grande** — recuerda no solo qué decisiones se tomaron sino *por qué*, permitiendo consistencia en proyectos de meses o años.

**Asistente personal con memoria persistente** — construye un mapa de conocimiento sobre el usuario que mejora con el uso. Caso real: Nova (mi asistente personal) usa NovaDB como su memoria desde hace semanas.

**Investigación y análisis** — un agente que acumula hallazgos de múltiples sesiones de investigación, conectando automáticamente conceptos relacionados sin intervención manual.

---

## Arquitectura Técnica

```
┌───────────────────────────────────────┐
│        Cualquier Agente LLM           │
│   (Claude, Gemini, GPT, Custom)       │
└──────────────┬────────────────────────┘
               │ MCP (Model Context Protocol)
┌──────────────▼────────────────────────┐
│       NovaDB MCP Server               │
│  14 herramientas · stdio transport     │
└──────────────┬────────────────────────┘
               │ Python API
┌──────────────▼────────────────────────┐
│          NovaDB Core                   │
│ Grafo Jerárquico · Búsqueda O(√N)     │
│ Consolidación 2F · Rebalanceo          │
└──────────────┬────────────────────────┘
               │ MessagePack / JSON
┌──────────────▼────────────────────────┐
│         Persistencia                   │
│  .msgpack (prod) · .json (debug)       │
└──────────────┬────────────────────────┘
               │ REST API (FastAPI)
┌──────────────▼────────────────────────┐
│          MindReader                    │
│ Astro + React + WebGL (Visor 3D)       │
└───────────────────────────────────────┘
```

---

## Estado Actual — Beta Funcional

**Implementado y operativo:**
- Motor de grafo semántico: **93 nodos, 934 conexiones, 13 categorías MACRO**
- Servidor MCP con **14 herramientas** integradas (memorizar, recordar, consolidar, analizar, exportar, etc.)
- Suite de **159 tests passing, 0 fallos** (core, búsqueda, consolidación, persistencia, decay, edge cases, integración, MCP)
- Auditoría de código completada — 23 hallazgos identificados, 6 críticos resueltos, 16 tests preexistentes corregidos
- **MindReader**: Visor 3D interactivo (Astro + React + FastAPI)
- Consolidación en **2 fases** (Proponer → Ejecutar) — diseño Human-in-the-loop
- Persistencia atómica en MessagePack y JSON con validación de dimensiones

**En exploración:**
- AlmaEmbed: arquitectura de red neuronal propia para embeddings locales (eliminar dependencia de APIs externas)

---

## Lo Que Busco

Asesoramiento y visión experta en:

**1. Validación técnica y académica** — ¿El enfoque jerárquico para memoria semántica y la complejidad O(√N) tienen bases sólidas? ¿Qué tan innovador es el uso de consolidación interactiva en 2 fases desde una perspectiva de ingeniería?

**2. Evaluación de potencial CITT** — Basado en el prototipo funcional actual, ¿considera que el proyecto tiene el perfil adecuado para postular al CITT? De ser así, ¿qué aspectos cree que deberían fortalecerse para una postulación exitosa?

**3. Orientación estratégica** — Más allá de lo técnico, ¿cuál considera que es el mejor camino para un proyecto con estas capacidades? (¿Foco en Open Source, incubadoras, o búsqueda de apoyo institucional para desarrollo D+I?)

---

*Documentación técnica completa disponible — PRD, SDD, análisis adversarial (red-teaming), demo script y repositorio con código fuente.*
