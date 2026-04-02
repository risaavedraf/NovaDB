# NovaDB 🧠✨

NovaDB es un **Motor de Memoria Semántica Jerárquica** diseñado para dotar a agentes de Inteligencia Artificial (y arquitecturas de software modernas) de una capacidad de memoria viva, estructurada y evolutiva.

Nace inicialmente como el "hipocampo" o disco duro cognitivo de la asistente *Alma Nova*, pero su arquitectura técnica es 100% agnóstica, permitiéndole ser el motor semántico de cualquier otro sistema.

---

## 🚀 El Problema que Resuelve

La memoria y almacenamiento tradicional falla en contextos de Inteligencia Artificial por falta de contexto o rigidez estructural:
- Las Bases de datos exactas (MongoDB, SQL) *no entienden la semántica*.
- Las Vector-DBs (ChromaDB) *carecen de jerarquía o relaciones naturales*.
- Las DB de Grafo puras (Neo4J) *requieren trabajo manual para enlazar conocimiento*.

**NovaDB une los 3 mundos:**
1. **Búsqueda Matemática (Cosenos):** Comparamos vectores matemáticos (embeddings) para entender *qué significa* el dato en vez de buscar texto exacto.
2. **Jerarquía Automática y Agentic:** Las memorias similares se atraen. Con suficiente gravitación semántica, el sistema exige (Fase 1) que un Agente IA las agrupe definitivamente en clusters (Fase 2).
3. **Persistencia Transparente:** Guarda en JSON limpio en tu SSD local para auditar, o en MessagePack para binarios ultrarrápidos listos para producción.

## 🏢 Las Tres Capas de NovaDB

- **MACRO:** Conceptos abarcadores inmensos (Ej: `Arquitecturas Cloud`, `Tecnologías del Startup`).
- **MEDIO:** Clúster de agrupamiento semántico inducido dinámicamente y nombrado por el agente. (Ej: `Amazon Web Services`, `Google Cloud`).
- **MEMORIA:** El dato atómico puro. (Ej: `A r1cky le pareció muy caro Lambda para procesos de 5min`).

---

## ⚙️ Cómo Comenzar

Clona este repositorio donde desees y ejecuta el ecosistema local de Nova en una burbuja limpia (venv). Alternativamente, usa `uv`.

### 1. Instalación
```powershell
# Crear y activar la burbuja (Windows)
python -m venv venv
.\venv\Scripts\activate

# Instalar los poderes mentales 
pip install -r requirements.txt
```

### 2. Configura tu Identidad (API KEY)
Crea un archivo `.env` en la raíz de la carpeta base y especifica:
```env
GEMINI_API_KEY=AIzaSyTuLlaveSeguraGigante...
```
Si no haces esto, NovaDB usará el embedder local (`sentence-transformers`) generador de 384 dimensiones.

### 3. Configuración de Logging (opcional)
Por defecto NovaDB usa el nivel INFO y guarda en un archivo si se opera dentro del servidor MCP para no ensuciar el stream:
```python
db = NovaDB(embedder=GeminiEmbedder(), log_file="./novadb.log", log_level="DEBUG")
```

---

## 🛠️ Estado del Proyecto y Roadmap

- [x] **Fase 1 (Core):** Implementación de clase base `Node`, búsqueda jerárquica O(√N), serialización JSON/MessagePack.
- [x] **Fase 2 (Consolidación Agentic v1.2):** Consolidador inteligente en dos fases (Proponer/Ejecutar) delegando el control de nombres a modelos de lenguaje o humanos.
- [x] **Fase 3 (Integración Nativa MCP):** Plug & Play para todo tipo de interfaces modernas.
- [x] **Fase 4 (Visualizador MindReader):** Visor en tiempo real 3D (React+Astro).

---

## 📋 Changelog

### v1.2 (2026-03-30)
- **Consolidación en 2 Fases:** Implementados los métodos `consolidar_proponer()` y `consolidar_ejecutar()`. Fin a los auto-grupos ruidosos, el agente IA o el humano escoge el nombre humano del clúster (MEDIO).
- **Hard-Link de MACRO:** Los nuevos nodos MEDIO ahora siempre buscan un padre MACRO automáticamente previniendo ser "huérfanos".
- **Nueva dependencia:** Compatibilidad con UV y servidores FastMCP estandarizados.

### v1.1 (2026-03-25)
- **Temporal decay:** Campo `relevancia` con decaimiento exponencial + access boost
- **Índices jerárquicos:** Búsqueda O(√N) garantizada, no solo aspiracional
- **Logging estricto:** File output para evitar corrupción del stream STDOUT durante comunicación de Model Context Protocol (MCP).

### v1.0 (2026-03-20)
- Release inicial con arquitectura de 3 capas (MACRO/MEDIO/MEMORIA)
- Consolidación automática offline.

---
_Mesa de diseño presidida, testeada y estructurada por **r1cky**._

