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
1. **Búsqueda Matemática (Cosenos):** Comparamos vectores para entender *qué significa* el dato en vez de buscar un texto exacto.
2. **Jerarquía Automática:** Las memorias similares se atraen. Con suficiente masa crítica algorítmica, el sistema exige que se agrupen solas.
3. **Persistencia Transparente:** Cero configuraciones pesadas. Guarda en JSON limpio en tu SSD local o en MessagePack para binarios ultrarrápidos.

## 🏢 Las Tres Capas de NovaDB

- **MACRO:** Conceptos abarcadores inmensos (Ej: `Arquitecturas Cloud`, `Tecnologías del Startup`).
- **MEDIO:** Clúster de agrupamiento semántico inducido dinámicamente. (Ej: `Amazon Web Services`, `Google Cloud`).
- **MEMORIA:** El dato quirúrgico puro. (Ej: `A r1cky le pareció muy caro Lambda para procesos de 5min`).

---

## ⚙️ Cómo Comenzar

Clona este repositorio donde desees y ejecuta el ecosistema local de Nova en una burbuja limpia (venv).

### 1. Instalación
```powershell
# Crear y activar la burbuja (Windows)
python -m venv venv
.\venv\Scripts\activate

# Instalar los poderes mentales (Google GenAI, Numpy, Dotenv, msgpack)
pip install -r requirements.txt
```

### 2. Configura tu Identidad (API KEY)
Debes crear un archivo `.env` en la raíz de la carpeta (ya está ignorado por GitHub, tu secreto está a salvo) y especificar:
```env
GEMINI_API_KEY=AIzaSyTuLlaveSeguraGigante...
```

### 3. Ejecuta la Prueba Diagnóstica Semántica
Verifica que tu modelo de búsqueda logre comprender la diferencia contextual entre "Gatos" y "SQL":
```powershell
python -m novadb.test.test_similitud
```

### 4. Configuración de Logging (opcional)
Por defecto NovaDB usa el nivel INFO y imprime a stdout:
```python
import logging
logging.getLogger("novadb").setLevel(logging.DEBUG)
```

O guardar a archivo:
```python
db = NovaDB(embedder=GeminiEmbedder(), log_file="./novadb.log", log_level="DEBUG")
```

---

## 🛠️ Estado del Proyecto y Roadmap

- [x] **Fase 1 (Core):** Implementación de clase base `Node`, búsqueda jerárquica O(√N), serialización JSON/MessagePack.
- [x] **Fase 2 (Consolidación Automática):** Consolidador con autobalanceo dinámico de jerarquía.
- [x] **Fase 3 (Integración Nativa):** Plug & Play en Alma Nova con `memory_manager.py`.
- [x] **Fase 4 (Pulido):** Decaimiento temporal, índices jerárquicos, type hints (~95%), logging estructurado.

---

## 📋 Changelog

### v1.1 (2026-03-25)
- **Temporal decay:** Campo `relevancia` con decaimiento exponencial + access boost
- **Índices jerárquicos:** Búsqueda O(√N) garantizada, no solo aspiracional
- **Type hints:** ~95% coverage con py.typed marker para mypy
- **Logging:** Reemplazado print() por Python logging módulo estructurado
- **98 tests nuevos:** 126 tests totales, todos pasando
- **Bugfix:** `get_mas_relevante()` renombrado correctamente
- **Nueva dependencia:** msgpack agregado a requirements.txt

### v1.0 (2026-03-20)
- Release inicial con arquitectura de 3 capas (MACRO/MEDIO/MEMORIA)
- Consolidación automática con threshold adaptativo
- Export a Markdown y MessagePack

---
_Mesa de diseño presidida, testeada y estructurada por **r1cky**._
