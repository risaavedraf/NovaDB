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
- Suite de **15 archivos de tests** (13 core + 2 MCP)
- **MindReader**: Visor 3D interactivo (Astro + React + FastAPI)
- Consolidación en **2 fases** (Proponer → Ejecutar) — diseño Human-in-the-loop
- Persistencia en MessagePack y JSON con validación de dimensiones

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
