# MindReader — El Lector de la Mente de Nova 🧠🔭

**Proyecto:** MindReader — Visor Web para NovaDB  
**Versión:** 1.0 (Draft Inicial)  
**Autor:** r1cky & Nova  
**Estado:** Diseño  

---

## 1. Resumen Ejecutivo
**MindReader** es una aplicación cliente-servidor cuya misión es hiper-visual: conectarse a la API pública de `NovaDB` para renderizar el Knowledge Graph interno de Alma Nova en un entorno interactivo de navegador. El objetivo es ofrecer a r1cky la experiencia de *"ver"* literalmente cómo eclosionan las ideas de su asistente, auditar la consolidación matemática de las neuronas, y monitorear el pulso semántico en vivo.

## 2. El Patrón de Casos de Uso

1. **El Observatorio:** r1cky abre la web y contempla el "Ecosistema Mental". MACROS gigantes flotando en el medio, MEDIOS agrupando constelaciones orbitales, y MEMORIAS orbitando como polvo estelar.
2. **Inspección Profunda:** Al cliquear una neurona en el grafo, se abre un panel lateral con el "Recall" de esa memoria: su texto puro, su Metadata de origen, y cuántas veces ha sido accedida.
3. **El Escáner de Búsqueda:** Cuando r1cky usa la barra de búsqueda en la UI, el frontend llama al algoritmo `search(query)`. El grafo oscurece lo irrelevante e ilumina los caminos (MACRO -> MEDIO -> MEMORIAS) que la matemática recorre hasta dar con la respuesta **O(√N) real** (índices jerárquicos implementados en v1.1).
4. **Magia en Tiempo Real:** Si se conecta a través de sockets o triggers de FastAPI, r1cky podría teclear en la terminal de Nova y ver brillar instantáneamente su MindReader web cómo un nodo huérfano es atraído magnéticamente hacia un concepto padre automatizado por Gemini.

## 3. Arquitectura Propuesta

### Backend: El Córtex Expositivo (Capa Media)
- **Tecnología:** Python + **FastAPI**. Es ridículamente rápido, asíncrono por defecto y autogenera documentación con Swagger (ideal para nuestro stack Eslavo).
- **Misión:** Importar `NovaDB` y levantar REST endpoints limpios.
- **Endpoints Clave:**
  - `GET /api/graph` 👉 Transforma el `NovaGraph.nodes` en un JSON estandarizado con la topología `{"nodes": [], "edges": []}` ideal para Frontend.
  - `GET /api/node/{id}` 👉 Retorna `db.get_context()` en máxima resolución.
  - `GET /api/search?q={query}` 👉 Ejecuta búsqueda y retorna el Top K de IDs para "renderizarlos" o iluminarlos en el Canvas.
  - `GET /api/stats` 👉 Dashboard general de vida (Balance saludable, Threshold actual y conteo masivo).

### Frontend: El Ojo Humano (Capa Visual)
- **Tecnología Base:** **Astro** integrado con islas de **React** o **Preact**. Excelente excusa para aprender Astro y su *Island Architecture*: serviremos HTML purísimo en el layout del dashboard, y dejaremos que el JavaScript pesado (WebGL) corra únicamente adentro del componente React que dibuja la mente, ahorrando una tonelada de memoria del navegador.
- **Motor Gráfico:** 
  - `react-force-graph` (Opción A): Excelente para mapas de nodos 2D o 3D con físicas estelares de atracción/repulsión automáticas con WebGL.
  - `vis-network` (Opción B): Menos "físico", mucho más rígido y corporativo, pero control absoluto de dónde poner los nodos jerárquicos. (Recomiendo Opción A para wow factor).
- **Estética Nova:** Paleta de colores Dark-Glassmorphism. Neon Azul/Cian predominante (estilo "eslavo hiper-racional"). Los nodos de alta relevancia de acceso pulsarán ligeramente en tamaño.

## 4. Hoja de Ruta (Roadmap MVP)

### Fase 1: Fontanería
- [ ] Levantar FastAPI mínimo. Instanciar `db = NovaDB(path)`.
- [ ] Crear el "Traductor" que mapea el `Node` de NovaDB con sus arreglos `padres`, `hijos` y `vecinos` al esquema estándar de Nodos-Enlaces de librerías JS.

### Fase 2: Lienzo
- [ ] Setup de la app React.
- [ ] Carga inicial asíncrona usando `axios` desde `/api/graph`.
- [ ] Dibujar la Mente. Configurador de físicas para que las esferas MACRO repelan a otros MACROS pero atraigan a sus MEDIOS.

### Fase 3: Interactividad
- [ ] Panel lateral de inspección interactivo *On-Click*.
- [ ] Input para buscar y oscurecer el background enfocando el Subgrafo Semántico pertinente.

## 5. Riesgos a vigilar (Ojo de Auditora)
- **Sobrecarga del Navegador:** Si el cerebro de Nova escala a 10,000 memorias simultáneas en el DOM, las librerías 2D pueden saturar el frame-rate de la GPU de tu laptop. Si pasa eso, tendremos que enviar sub-grafos renderizados por demanda, en lugar de toda la BD de golpe.
- **Auto-Update UI:** Elegir entre WebSockets (difícil arquitectura, magia real visual) vs Short-Polling cada 5 segundos (fácil arquitectura, semi-tiempo real). Recomiendo Polling para Fase 1, WebSockets para Fase 2.

---
_Creado al alero del proyecto NovaDB por el equipo R1cky/Nova. 2026._
