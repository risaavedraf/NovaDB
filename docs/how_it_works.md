# Cómo funciona NovaDB

## El Problema

Las bases de datos tradicionales fallan al intentar ser la "memoria" de una IA:

- **SQL/MongoDB** — Solo coincidencias exactas. Si preguntas "¿qué me gusta?" y no almacenaste esa cadena exacta, no devuelve nada.
- **Bases de Datos Vectoriales** (ChromaDB) — Entienden el significado semántico pero no tienen estructura. Son listas planas de vectores sin relaciones jerárquicas padre-hijo.
- **Bases de Datos de Grafos** (Neo4j) — Tienen relaciones poderosas pero requieren conexiones manuales. No tienen agrupamiento (clustering) automático.

NovaDB combina las tres aproximaciones.

## Las Tres Capas

Cada pieza de conocimiento vive en uno de los tres niveles:

### MACRO — El Contexto Global
Conceptos abstractos que abarcan múltiples dominios. Piensa en "Arquitecturas Cloud" o "Tecnologías de Startups", "Perfil del Usuario", "Proyectos Personales". Estos son los centros gravitacionales del grafo de conocimiento.

### MEDIO — El Clúster
Agrupaciones naturales que emergen de la similitud semántica. "Servicios de AWS", "Lenguajes de Programación", "Desarrollo de Space Colonizer". Estos se forman de manera semi-automática a través del Agente (Fase 1 y Fase 2 de Consolidación).

### MEMORIA — El Detalle
Hechos quirúrgicos y atómicos. "r1cky pensó que Lambda era muy caro para un proceso de 5 minutos". Aquí es donde vive el conocimiento crudo.

## Cómo se Agrupan las Memorias (Consolidación Agentic)

1. Guardas una memoria con texto → Gemini (o el modelo local) lo convierte en un vector matemático.
2. NovaDB compara el vector contra los nodos existentes utilizando **similitud coseno**.
3. Si la similitud supera un umbral → la nueva memoria se ancla temporalmente al MACRO o MEDIO que mejor coincida, o queda como "huérfana" orbitando cerca de sus vecinos.
4. **Fase 1 (Proponer)** → El motor analiza qué memorias huérfanas están muy cerca unas de otras (formando constelaciones) y le propone al Agente IA agruparlas.
5. **Fase 2 (Ejecutar)** → El Agente IA aprueba el clúster, decide un nombre humano para él, y NovaDB crea un nuevo nodo MEDIO, conectándolo dinámicamente al MACRO padre más similar para mantener la gravedad del sistema.

Esto es **jerarquía inducida** — una estructura que se construye y organiza a sí misma de manera orgánica, con supervisión humana/agentic.

## Decaimiento Temporal (Olvido Gradual)

Las memorias tienen un puntaje de `relevancia` que decae con el tiempo, imitando al cerebro humano:

- Las memorias frescas tienen mayor puntaje.
- Las memorias consultadas frecuentemente reciben un impulso (boost) de relevancia.
- El sistema de rebalanceo prioriza y organiza el árbol basándose en estos puntajes.

## Búsqueda: O(√N) Garantizado

Una búsqueda lineal tradicional revisa cada nodo. NovaDB utiliza índices jerárquicos:

1. Compara la consulta espacialmente contra los nodos MACRO primero (son los menos).
2. Profundiza en los nodos MEDIO del MACRO ganador.
3. Profundiza en las MEMORIAS del MEDIO ganador.

Resultado: **Tiempo de búsqueda O(√N)** sin importar el tamaño gigantesco que alcance el grafo.

## Persistencia Binaria

Dos formatos disponibles:
- **JSON** — Legible por humanos, excelente para debugging y auditorías.
- **MessagePack** — Formato binario ultrarrápido, compacto y optimizado, recomendado para producción.
