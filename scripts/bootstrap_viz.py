import os
import sys
from novadb.novadb import NovaDB
import numpy as np

# Configuración del Embedder Dummy
from novadb.core.embedder import BaseEmbedder
class MockVizEmbedder(BaseEmbedder):
    def encode(self, text: str):
        # Generar vectores que "orbiten" segun el texto
        np.random.seed(sum(ord(c) for c in text))
        return np.random.rand(768).astype(np.float32)

def bootstrap():
    db_path = "./db/nova_production.msgpack"
    if os.path.exists(db_path): os.remove(db_path)
    os.makedirs("./db", exist_ok=True)
    
    db = NovaDB(embedder=MockVizEmbedder(), path=db_path)
    
    # 1. MACROS (Grandes polígonos)
    m1 = db.insert("Filosofía Eslava y Rigor", tipo="MACRO")
    m2 = db.insert("Arquitectura de Software Moderna", tipo="MACRO")
    m3 = db.insert("Personal Projects", tipo="MACRO")
    
    # 2. MEDIOS (Agrupadores)
    md1 = db.insert("Teoría de Grafos y Topología", tipo="MEDIO")
    md2 = db.insert("Seguridad y Criptografía", tipo="MEDIO")
    md3 = db.insert("Hitos del Proyecto", tipo="MEDIO")
    
    # Conexiones manuales (Puentes)
    db.connect(m1, md1, "CONCEPTO_BASE")
    db.connect(m2, md2, "FRAMEWORK")
    db.connect(m3, md3, "HISTORIA")
    
    # 3. MEMORIAS (El polvo de estrellas)
    memorias_m1 = [
        "El estoicismo esclavo se diferencia por su resiliencia ante el invierno.",
        "La lógica de predicados es el cimiento de cualquier pensamiento atómico.",
        "Dostoievski exploraba la dualidad de la psique, algo que queremos en Nova."
    ]
    for text in memorias_m1: db.insert(text, tipo="MEMORIA")
    
    memorias_m2 = [
        "NovaDB usa MessagePack para serialización binaria ultrarrápida.",
        "FastAPI es el puente ideal para el visor web de MindReader.",
        "Astro y React permiten una visualización reactiva con Island Architecture."
    ]
    for text in memorias_m2: db.insert(text, tipo="MEMORIA")
    
    memorias_m3 = [
        "NovaDB bootstrapped its first functional digital hippocampus.",
        "Nova aims to be your second mind, augmenting human memory.",
        "The Mind Reader project was born from pure curiosity about knowledge graphs."
    ]
    for text in memorias_m3: db.insert(text, tipo="MEMORIA")
    
    db.save()
    print(f"✅ Cerebro de prueba creado en {db_path} con {db.stats()['total_nodos']} neuronas.")

if __name__ == "__main__":
    bootstrap()
