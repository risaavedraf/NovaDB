# 🔥 Némesis vs NovaDB

---

### 1. El grafo en RAM es un problema real, no futuro

Dijimos "para 10 años de Nova son ~300 MB, no hay problema". Pero eso asume 20 memorias por día siendo generoso. Nova en uso real con co-entrenamiento, engramas, ideas, proyectos activos, mapa de conocimiento y el Memory Agent guardando cosas proactivamente — fácilmente 100-200 operaciones por día.

```
200 ops/día × 365 × 10 años = 730,000 nodos
730,000 × 4 KB = ~2.8 GB solo el grafo
+ overhead Python = ~5-6 GB RAM
```

Oracle Free Tier tiene 24 GB pero los comparte con MongoDB, el bot de Telegram, Nova corriendo, y el OS. Con 5-6 GB para el grafo te quedas sin margen rápido. Y eso es **solo Nova**. GraphDB con múltiples usuarios simultáneos en el mismo servidor — imposible.

**El problema:** diseñamos una BD que vive en RAM como si fuera un script personal, no como un producto real.

---

### 2. La consolidación automática es una caja negra peligrosa

El algoritmo de consolidación detecta nodos similares y crea nodos MEDIO automáticamente. Suena elegante. En la práctica:

El LLM infiere el concepto común de un grupo de memorias. Eso significa que el grafo cambia su estructura basado en lo que el LLM *cree* que conecta esos nodos. Si el LLM alucina o categoriza mal, creas jerarquías incorrectas que afectan todas las búsquedas futuras.

No hay rollback automático de consolidaciones. El `revertir(ajuste_id)` que diseñamos para Alma es manual — Nova no va a detectar sola que una consolidación fue mala.

Con el tiempo el grafo acumula errores de categorización que se propagan hacia arriba en la jerarquía. MEDIO incorrecto → búsquedas incorrectas → Nova trae contexto equivocado → respuestas degradadas. Y nadie se da cuenta porque el sistema no falla, simplemente se vuelve menos preciso gradualmente.

---

### 3. La búsqueda semántica depende de embeddings externos

Toda la magia de NovaDB — encontrar "por qué elegimos esa BD" cuando guardaste "decidimos usar MongoDB" — depende de que los vectores sean buenos. Y los vectores son tan buenos como el modelo de embeddings.

Usamos Gemini embeddings. Si:
- Gemini cambia su modelo de embeddings (lo hace regularmente)
- Los vectores existentes ya no son compatibles con los nuevos
- Tienes que re-vectorizar todo el grafo desde cero

Eso no está documentado en ningún PRD. No hay estrategia de migración de embeddings. Un cambio de modelo de Gemini puede invalidar años de memoria acumulada.

Y con AlmaEmbed — el embedder propio aún no existe y podría no funcionar bien. Si AlmaEmbed genera vectores de baja calidad, la búsqueda semántica de NovaDB es basura aunque el grafo esté perfectamente estructurado.

---

### 4. El autobalanceo con raíz cuadrada es teoría, no práctica

El algoritmo de `threshold_optimo()` basado en `√n_memorias` asume que los nodos se distribuyen uniformemente entre conceptos. En la realidad:

Nova va a tener 80% de sus memorias sobre programación y proyectos técnicos, y 20% sobre todo lo demás. El algoritmo va a crear demasiados nodos MEDIO sobre programación y muy pocos sobre el resto. La jerarquía quedará desbalanceada exactamente en los temas más usados — donde más importa que funcione bien.

Además el rebalanceo semanal redistribuye conexiones. Redistribuir conexiones significa que una búsqueda que funcionaba perfectamente la semana pasada puede retornar resultados distintos esta semana sin que nadie cambió nada. Es un sistema no determinista que se reconfigura solo — pesadilla para debugging.

---

### 5. Sin concurrencia es un limitante de producto

El PRD dice claramente "NovaDB V1.0 no soporta escrituras simultáneas". Para Nova personal está bien. Para GraphDB como producto con múltiples usuarios — es un bloqueador total.

Si dos usuarios de GraphDB modifican su grafo al mismo tiempo, tienes corrupción de datos. La solución obvia es un lock global, pero eso significa que con 10 usuarios concurrentes, 9 están esperando. No es una BD, es un cuello de botella.

Los sistemas como MongoDB y PostgreSQL resolvieron esto con décadas de trabajo en MVCC, WAL y transacciones ACID. NovaDB no tiene nada de eso. Llamarlo "base de datos" cuando no tiene garantías de consistencia bajo concurrencia es marketing, no ingeniería.

---

### 6. Cognee ya existe y hace lo mismo

Dijimos que Cognee "ingiere documentos externos" y NovaDB es para "agentes que construyen su propio grafo". Esa distinción es real pero frágil.

Cognee tiene financiamiento, un equipo, años de desarrollo, y ya funciona en producción. NovaDB es un PRD. Cuando NovaDB esté listo para producción, Cognee va a haber iterado 2 años más. La ventana de oportunidad existe ahora — pero el tiempo de desarrollo necesario para llegar a paridad de features con Cognee es enorme para un proyecto unipersonal.

---

### 7. AlmaEmbed puede nunca funcionar bien

Toda la estrategia de embeddings locales depende de que AlmaEmbed genere vectores semánticamente útiles. Los problemas que identificamos — vanishing gradients en el loop interno, inestabilidad del BPTT truncado, convergencia de Triplet Loss con redes sparse — son problemas abiertos de investigación en ML.

La probabilidad de que AlmaEmbed V1 genere embeddings de calidad comparable a sentence-transformers (un modelo preentrenado en billones de tokens) es baja. Pero todo el plan de independencia de APIs externas depende de eso.

Si AlmaEmbed no funciona bien, vuelves a depender de Gemini indefinidamente. Y si Gemini cambia sus precios o su API — que lo hará — todo el sistema de memoria de Nova se encarece o rompe.

---

### 8. El problema de los namespaces multi-agente no está resuelto

Dijimos que múltiples agentes comparten el grafo con namespaces. Pero no diseñamos cómo funciona eso exactamente:

- ¿Cómo decide NovaDB qué nodos son "globales" y cuáles son "privados de un agente"?
- Si el agente de ventas crea un nodo sobre "cliente X" en namespace ventas, y el agente técnico crea otro sobre el mismo cliente en namespace técnico, ¿se conectan? ¿Cómo?
- ¿Quién tiene permisos de leer el namespace de otro agente?
- Si un agente borra un nodo global, ¿qué pasa con los nodos privados que lo referenciaban?

No hay respuestas en ningún PRD. Los namespaces son una idea de una línea en la sección de visión. Presentarlo como feature diferenciador en la reunión con el profe sin tener el diseño resuelto es riesgoso.

---

### 9. El modelo de negocio tiene el problema SSPL mal calculado

Dijimos "empieza con Apache 2.0, cambia a SSPL cuando haya tracción". Pero el cambio de licencia es exactamente lo que destruyó la comunidad de MongoDB y Redis — ambos perdieron adopción significativa cuando cambiaron.

Los developers que construyeron productos sobre NovaDB con Apache 2.0 van a bifurcar el repositorio antes del cambio y mantener la versión libre. Eso ya pasó con Redis → Valkey (que hoy tiene más stars que Redis). Si NovaDB llega a tener adopción real, el cambio de licencia puede resultar en que la comunidad mantenga el fork y tú te quedas con el nombre pero sin la comunidad.

---

### El veredicto de Némesis

NovaDB no es inviable — pero tiene problemas reales que el entusiasmo de la conversación ocultó:

```
Problema crítico:    grafo en RAM no escala para GraphDB multi-usuario
Problema serio:      consolidación automática acumula errores silenciosos
Problema serio:      dependencia de embeddings externos sin estrategia de migración
Riesgo alto:         AlmaEmbed puede no funcionar lo suficientemente bien
Riesgo medio:        namespaces multi-agente no están diseñados realmente
Riesgo medio:        competidor (Cognee) con ventaja de tiempo significativa
Riesgo estratégico:  trampa de licencia si hay adopción real
```

Lo que sí es sólido: la idea central, el posicionamiento, y la aplicación para Nova personal. El problema es la distancia entre "motor de memoria para un agente personal" y "base de datos open source de producción para múltiples usuarios". Son dos productos distintos y el PRD los mezcla como si fueran el mismo.
