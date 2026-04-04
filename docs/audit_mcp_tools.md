# 🔌 Auditoría de Capa MCP — NovaDB v1.1.0

**Fecha**: 2026-04-02  
**Auditor**: Nova  
**Alcance**: Submódulo `novadb-mcp/src/novadb_mcp/tools/*.py`

El Model Context Protocol (MCP) expone tu motor de memoria directamente al LLM. Cuando el LLM invoca una herramienta, espera una interfaz predecible, segura y transaccional. A continuación, el análisis de las herramientas actuales y su nivel de integración con FastMCP.

---

## 🚨 Vulnerabilidades Críticas

### 1. Data Race en Persistencia (Corrupción de Disco)
**Componente**: Todos los tools transaccionales (`memorizar`, `actualizar`, `conectar`, `consolidar_ejecutar`)  
**Archivos**: `memoria.py`, `contexto.py`, `sistema.py`

**El Problema**:
Todos los llamados que modifican el grafo terminan en un `db.save(get_config().db_path)`. El servidor FastMCP puede procesar múltiples requests en paralelo (multihilo/asíncrono). Si dos agentes (o dos tools en paralelo) llaman a `memorizar` o `actualizar` simultáneamente:
1. Hilo A abre `db_path` en modo escritura binaria (`wb`).
2. Hilo B abre el mismo archivo en `wb` antes de que A termine.
3. **Resultado**: Archivo `.msgpack` trunco o corrupto. El motor pierde toda la memoria.

**Solución**:
Implementar un "file lock" (ej. `filelock` de Python) al hacer `db.save()` y hacer la escritura atómica (escribir a `.tmp` y luego renombrar) en `disk.py`.

> **⚡ PARCIALMENTE RESUELTO (2026-04-04)**: La escritura atómica está implementada (`disk.py` escribe a `.tmp` + `os.replace()`). Esto previene corrupción del archivo en crash. Falta el file lock para prevenir writes concurrentes de múltiples hilos.

---

### 2. Path Traversal en `admin.py` (Vulnerabilidad de Host)
**Componente**: Herramientas de sistema  
**Archivos**: `admin.py` (`guardar`, `cargar`, `exportar`)

```python
def exportar(ruta: str) -> Dict[str, Any]:
    db.export_md(ruta)
```

**El Problema**:
Las herramientas `guardar()`, `cargar()` y `exportar()` reciben un argumento opcional u obligatorio `ruta` directamente del LLM. No hay sanitización ni validación de confines ("sandbox").
Un agente rebelde o confundido podría recibir un prompt inyectado, y llamar a `exportar(ruta="/etc/passwd")` (en Linux) o `exportar(ruta="C:\Windows\System32\hal.dll")`, corrompiendo el sistema anfitrión o leyendo ubicaciones sensibles.

**Solución**:
Restringir rigurosamente estas herramientas a un único directorio predefinido (ej. `./db/exports/`) asegurándose de validar la ruta canónica.

---

## 🟡 Problemas Medios e Insidiosos

### 3. Falsos Positivos en Feedback de Ejecución
**Componente**: Herramienta `actualizar`  
**Archivo**: `contexto.py`

```python
db.update(node_id=node_id, fields=fields)
db.save(get_config().db_path)
return {"success": True, "message": f"✅ Nodo {node_id} actualizado"}
```

**El Problema**:
Dentro del core, el método `NovaDB.update()` tiene una cláusula: `if not nodo: return`. Si el ID solicitado no existe, no hace nada. PERO la herramienta MCP devuelve success y "Nodo actualizado".
El LLM pensará erróneamente que los datos se han guardado e intentará proseguir. El LLM es súper dependiente del feedback literal. Si le dices que falló, lo corrige; si le mientes, se desvía del objetivo.

**Solución**:
Retornar error si el nodo no existe. Idealmente `get_node()` o `update()` debe retornar un booleano para validar el estado.

---

### 4. Schemas Indefinidos para el LLM
**Componente**: Decoradores `@mcp.tool`  
**Archivo**: Todos los decorators

```python
def _memorizar(texto: str, tipo: str = "MEMORIA", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
```

**El Problema**:
Al usar `Dict[str, Any]` (tipos nativos de Python), FastMCP genera un JSON Schema vacío o demasiado genérico para el argumento `metadata`. El LLM no va a saber con certeza qué claves componen una metadata bien formada.
A diferencia de un cliente humano, MCP se basa en Schemas.

**Solución**:
Usar `pydantic.BaseModel` para tipar con precisión los kwargs más complejos y lograr que los agentes MCP reciban buenas descripciones de campo.

---

## 🟢 Mejoras de Entorno (Menores)

### 5. Fragmentación de Repetición (DRY)
**Componente**: Imports espaguetis  
La línea `sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))` seguida de una re-adquisición de la db `db = get_db()` se copia 4 veces para poder saltar la arquitectura.
Las herramientas dependen individualmente de saber dónde se guarda (`db.save(get_config().db_path)`), acoplando las herramientas a la infraestructura de disco local en vez de que NovaDB lo auto-gestione al insertar/modificar si tiene el `autosave=True`.

**Sugerencia**:
Instalar NovaDB en modo *editable* en el entorno MCP o setear `autosave=True` para que sea el Motor el encargado de guardar, liberando a las Tools de tener llamar a `db.save()` directamente.
