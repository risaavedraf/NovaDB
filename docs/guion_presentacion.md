# 🎙️ Guión de Presentación — NovaDB

> **Para estudiar antes de la reunión con el profe.**
> Cada sección tiene el *guión* de lo que dices y las *notas* de lo que debes saber si te preguntan algo. No memorices el guión al pie de la letra — entiende las ideas y cuéntalo con tus propias palabras.

---

## 📌 Estructura General (tiempo estimado: 20–25 min)

| # | Sección | Tiempo |
|---|---|---|
| 1 | Gancho — El Problema | 2 min |
| 2 | La Solución — Qué es NovaDB | 3 min |
| 3 | Arquitectura Técnica | 5 min |
| 4 | Demo en Vivo | 7 min |
| 5 | Estado Actual y Proyecciones | 3 min |
| 6 | Preguntas que te puede hacer | libre |

---

## 1. 🎯 Gancho — El Problema (2 min)

**Lo que dices:**

> "Voy a empezar con una pregunta simple: ¿cuánto recuerda realmente un agente de IA?"
>
> "Hoy, si usas Claude, Gemini o cualquier LLM, recuerda lo que le dijiste hace cinco minutos dentro de la misma conversación. Pero mañana, empieza desde cero. Para una tarea puntual está bien. Pero para un proyecto de meses, un asistente empresarial, o múltiples agentes colaborando, ese olvido sistemático es un problema crítico."
>
> "Las soluciones que existen toman uno de dos caminos: guardan un resumen que se degrada con el tiempo, o guardan hechos aislados en una lista plana sin entender cómo se relacionan. NovaDB es mi propuesta para resolver eso de raíz."

**Notas:**
- El problema es real — es el "Lost in the Middle" problem documentado en la literatura.
- Si el profe lo conoce, ganaste credibilidad al nombrarlo.

---

## 2. 💡 La Solución — Qué es NovaDB (3 min)

**Lo que dices:**

> "NovaDB es un Motor de Memoria Semántica Jerárquica para agentes de IA. Combina en un solo motor lo que normalmente requeriría tres tecnologías separadas."
>
> "SQL busca texto exacto. ChromaDB entiende semántica pero es una lista plana. Neo4j tiene relaciones pero requieren definición manual. NovaDB toma lo mejor de las tres: semántica vectorial, jerarquía automática, y relaciones que emergen solas."

**Frase clave — apréndela:**
> *"Los sistemas actuales guardan hechos. NovaDB guarda conocimiento — con las conexiones que hacen que ese conocimiento sea útil."*

---

## 3. 🏗️ Arquitectura Técnica (5 min)

### Las Tres Capas

> "La jerarquía tiene tres niveles."
>
> "**MACRO**: conceptos abstractos amplios — 'Arquitecturas Cloud', 'Proyectos del Usuario'. Los continentes del mapa."
>
> "**MEDIO**: clústeres — 'Servicios de AWS'. Se crean automáticamente cuando el motor detecta memorias semánticamente similares acumulándose."
>
> "**MEMORIA**: hechos atómicos — 'Lambda resultó caro para procesos de 5 minutos'."

### Búsqueda O(√N)

> "La jerarquía tiene una consecuencia matemática directa: la búsqueda no es lineal. Navego del MACRO más cercano → al MEDIO → a las MEMORIAs candidatas. Si tengo N nodos en grupos de √N, recorro √N grupos + √N elementos. Con 10.000 nodos: 200 operaciones en vez de 10.000."

**Sé preciso:** el peor caso sigue siendo O(N). El Rebalancer es el que mantiene el árbol balanceado para que el caso promedio se aproxime a O(√N).

### Consolidación 2 Fases (Human-in-the-loop)

> "Las memorias huérfanas se acumulan. El motor detecta cuáles están cerca semánticamente y propone agruparlas — Fase 1. En vez de nombrarlas automáticamente con un nombre algorítmico genérico, le pregunta al agente: '¿cómo llamas esto?' El agente decide, y se ejecuta — Fase 2. Automatizo la detección, el agente supervisa la categorización."

### Capa MCP

> "Para integración zero-code, implementé un servidor MCP — el estándar abierto de Anthropic 2024. 14 herramientas que cualquier agente compatible puede invocar directamente: Claude, Gemini, GPT."

---

## 4. 🖥️ Demo en Vivo (7 min)

> ⚠️ Practícalo varias veces. Esta es la parte que más impresiona.

**Paso 1 (30s) — Mostrar MindReader:**
> "Este es el grafo de conocimiento de mi asistente personal en producción real. 93 nodos, 934 conexiones, 13 MACROs."

**Paso 2 (60s) — Insertar memoria:**
> "Guardo un dato ahora mismo. [Inserta algo.] Ya está en el grafo — anclado al MACRO más cercano."

**Paso 3 (60s) — Búsqueda semántica:**
> "Busco sin palabras exactas. [Consulta vaga.] Navegó del MACRO al MEDIO al clúster. No fue lineal."

**Paso 4 (90s) — Consolidación:**
> "Le pido al agente que agrupe lo que puede agrupar. Propone, yo nombre, ejecuta. Mira el grafo — los huérfanos tienen un MEDIO padre ahora."

**Paso 5 (30s) — `analizar`:**
> "Radiografía completa: balance ratio, huérfanos, vecinos promedio, decay rate."

---

## 5. 📊 Estado Actual (3 min)

> "Beta funcional. Motor core completo, 14 herramientas MCP, 15 archivos de tests, MindReader operativo."
>
> "Lo que busco en esta reunión: ¿el enfoque jerárquico tiene bases académicas sólidas? ¿Tiene perfil para CITT o incubadora? Necesito una visión experta para priorizar el próximo paso."

---

## 6. 🔥 Preguntas que El Profe Puede Hacer

**"¿O(√N) es real o solo teórico?"**
> El Rebalancer detecta MACROs sobrecargados (más de `grupo_ideal * 1.5` hijos) y redistribuye. El peor caso es O(N), pero el sistema tiene mecanismos activos para evitar llegar ahí.

**"¿Diferencia real con LangChain Memory o MemoryGPT?"**
> LangChain Memory es un buffer lineal sin estructura. MemoryGPT usa paginación pero sigue siendo plano. NovaDB tiene jerarquía inducida y búsqueda sublineal — eso no existe en esas implementaciones.

**"¿Por qué Python y no Rust?"**
> El ecosistema de IA es Python. El cuello de botella real es la latencia de la API de embeddings, no el código. Para un prototipo académico, la prioridad fue la correctitud arquitectural.

**"¿Consistencia con múltiples agentes?"**
> Hoy asume un agente a la vez — es una limitación conocida. Si escalara a multi-agente, el siguiente paso sería file locking y escritura atómica (WAL pattern).

**"¿Qué tan original es? ¿Hay papers?"**
> Hay trabajo en Hierarchical Semantic Memory y Knowledge Graph construction automático. La contribución de NovaDB es la combinación: jerarquía inducida + consolidación human-in-the-loop + MCP nativo. La combinación es lo nuevo.

**"¿Por qué similitud coseno?"**
> Mide el ángulo entre vectores — similitud de significado independiente de la magnitud. La distancia euclidiana en alta dimensión sufre la "maldición de la dimensionalidad". Coseno es el estándar para texto y embeddings.

---

## 7. 🧠 Conceptos Que Debes Dominar

| Concepto | Lo que debes saber decir |
|---|---|
| **Similitud Coseno** | Ángulo entre vectores. 0–1. 1 = idéntico en significado. |
| **Embedding** | Vector numérico que representa texto en espacio de alta dimensión (768 dims con Gemini). |
| **O(√N)** | √N grupos de √N elementos = 2×√N operaciones vs N lineales. |
| **MCP** | Estándar abierto para herramientas de agentes. stdio transport. Anthropic 2024. |
| **Decaimiento temporal** | `relevancia *= exp(-decay_rate * horas)` — olvido gradual. |
| **Human-in-the-loop** | Automatizo detección, el agente/humano supervisa la decisión. |
| **Maldición de la dimensionalidad** | En alta dimensión, distancias euclidianas pierden discriminación. Por eso coseno. |

---

*La llevas r1cky. 🧠✨*
