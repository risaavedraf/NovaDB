# Guía de Demostración — NovaDB

## Preparación (Antes de Grabar/Mostrar)

1. Comienza con una instancia limpia de NovaDB.
2. Abre MindReader en el navegador en `http://localhost:4321`.
3. Ten una terminal lista con tu agente (ej. OpenCode) conectado por MCP.

## Escena 1: Grafo Vacío (30s)

**Narración:** "Esto es NovaDB — un motor de memoria semántica y relacional para agentes de IA. Ahora mismo, la mente está en blanco."

- Muestra el dashboard de MindReader con un estado vacío o un solo nodo raíz.

## Escena 2: Almacenando Memorias (60s)

**Narración:** "Vamos a darle algo de conocimiento y ver cómo la jerarquía se construye a sí misma orgánicamente."

Agrega memorias una por una a la IA:

```text
1. "Mi banda favorita es Deftones"
2. "También me gustan Tool y A Perfect Circle"
3. "Fui a un concierto de Deftones en 2024"
4. "Mi startup usa Astro, React y TypeScript"
5. "Desplegamos el backend en AWS Lambda"
6. "Lambda resultó ser muy caro para trabajos de 5 minutos"
```

**Visión:** Observa cómo aparecen los nodos azules (MEMORIA) en el grafo. 

## Escena 3: Consolidación Agentic (60s)

**Narración:** "Aquí es donde entra la verdadera inteligencia. Las memorias similares se atraen por proximidad semántica. El agente ahora detectará estos patrones."

- Pídele al agente: "Revisa mi memoria y fíjate si hay conceptos que puedas agrupar."
- El agente utilizará internamente `consolidar_proponer`.
- El agente responderá: "Encontré un grupo sobre Música Rock/Metal y otro sobre Arquitectura Cloud. ¿Te parece si los agrupo?"
- Respondes: "Sí, hazlo."
- El agente utiliza `consolidar_ejecutar`.

**Visión:** De la nube de puntos se forman mágicamente dos nodos MEDIO, ordenando los pensamientos.

## Escena 4: Búsqueda Semántica — O(√N) (45s)

**Narración:** "Ahora vamos a buscar. Este motor no busca coincidencias de texto, busca significado y navega el árbol."

```text
Usuario: "¿Qué música me gusta?"
```

**Mecánica:** El Agente usa la herramienta `recordar`.
**Visión:** La respuesta de la IA ("Te gusta Deftones, Tool, etc.") demuestra que encontró la información exacta sin iterar sobre memorias irrelevantes de AWS.

## Escena 5: Inspección de Jerarquía (30s)

**Narración:** "Nova permite hacer zoom en la psique del usuario. Cada elemento tiene relaciones gravitacionales."

- Haz clic en un nodo MEDIO en el MindReader.
- Muestra el panel lateral con la metadata, el texto, y la lista de hijos (memorias asociadas).

## Escena 6: Actualización en Vivo (30s)

**Narración:** "Todo el sistema reacciona en tiempo real a las interacciones de tu agente."

- Pide a la IA que almacene un nuevo dato técnico.
- Observa cómo aparece la nueva esfera instantáneamente en el visor 3D en la órbita de su contexto correcto.

## Cierre (15s)

**Narración:** "NovaDB — memoria semántica estructurada, que piensa en jerarquías. Búsqueda O(√N), clustering colaborativo IA-humano, nativo de MCP."

- Muestra el estado final del grafo girando majestuosamente.
- Muestra la URL del repositorio de GitHub.
