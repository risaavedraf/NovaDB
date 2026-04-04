import os
import sys
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware

# Importamos el Core de NovaDB desde el nivel superior
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from novadb.novadb import NovaDB

app = FastAPI(title="MindReader API de Nova")

# 1. PARCHE CORS RESTRINGIDO
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321", "http://localhost:3000", "http://127.0.0.1:4321", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# 2. PARCHE AUTENTICACION BASE
API_KEY = os.getenv("MINDREADER_SECRET")
if not API_KEY:
    print("[WARNING] MINDREADER_SECRET no configurado. El API queda sin autenticación. "
          "Seteá la variable de entorno para producción.")

async def verify_api_key(x_api_key: str = Header(None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Acceso denegado a la mente de Nova.")
    return x_api_key

# Levantamos la base de datos oficial (o la de E2E si no hemos inyectado nada)
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db', 'nova_production.msgpack'))
if not os.path.exists(db_path):
    print(f"[WARNING] Base prod no encontrada: {db_path}. Fallback a BD vacia o e2e")
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'e2e_test_db.msgpack'))

db = NovaDB(path=db_path, autosave=False) # Lectura pura para el visor web

@app.get("/api/stats", dependencies=[Depends(verify_api_key)])
def get_stats():
    return db.stats()

import numpy as np

def cosine_sim(v1, v2):
    if v1 is None or v2 is None: return 0.5
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0: return 0
    return float(np.dot(v1, v2) / (norm1 * norm2))

@app.get("/api/graph", dependencies=[Depends(verify_api_key)])
def get_graph():
    """
    Retorna la topología completa en formato 3D Network.
    Mapeo de Grupos: 1(MACRO), 2(MEDIO), 3(MEMORIA).
    """
    nodes = []
    links = []
    
    for nid, n in db.graph.nodes.items():
        # Atributos estelares
        group = 1 if n.tipo == "MACRO" else (2 if n.tipo == "MEDIO" else 3)
        val = 20 if group == 1 else (10 if group == 2 else 3) # Tamaño de la esfera
        
        nodes.append({
            "id": nid,
            "name": n.text[:80] + "..." if len(n.text)>80 else n.text,
            "group": group,
            "val": val,
            "tipo": n.tipo,
            "accesos": n.accesos
        })
        
        # Enlaces Gravitacionales con Similitud Real
        for h_id in n.hijos:
            h_node = db.graph.nodes.get(h_id)
            sim = cosine_sim(n.vector, h_node.vector) if h_node else 0.5
            links.append({
                "source": nid, 
                "target": h_id, 
                "value": sim * 3, # Escalar para grosor visual
                "label": f"Familiaridad: {sim:.2f}",
                "sim": sim
            })
            
        for v_id in n.vecinos:
            v_node = db.graph.nodes.get(v_id)
            sim = cosine_sim(n.vector, v_node.vector) if v_node else 0.4
            links.append({
                "source": nid, 
                "target": v_id, 
                "value": sim, 
                "label": f"Familiaridad: {sim:.2f}",
                "sim": sim
            })
            
        for conn in n.conexiones:
            # Puentes definidos manualmente
            links.append({"source": nid, "target": conn["target"], "value": conn.get("peso", 1.0)})
            
    return {"nodes": nodes, "links": links}

@app.get("/api/node/{node_id}", dependencies=[Depends(verify_api_key)])
def get_node_context(node_id: str):
    return db.get_context(node_id)
