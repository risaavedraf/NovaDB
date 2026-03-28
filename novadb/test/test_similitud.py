import os
import numpy as np
from novadb.core.graph import similitud_coseno
from novadb.core.embedder import GeminiEmbedder

print("--- PRUEBA 1: MATEMÁTICA PURA (SIN API) ---")
# Vectores inventados (imaginemos que tienen 3 dimensiones en vez de 768)
vector_a = np.array([1.0, 0.0, 0.0])  # Apunta al eje X
vector_b = np.array([1.0, 0.0, 0.0])  # Idéntico a A
vector_c = np.array([0.0, 1.0, 0.0])  # Apunta al eje Y (90 grados de A)

print(f"Similitud A vs B (Mismos números): {similitud_coseno(vector_a, vector_b)}") # Debería ser 1.0
print(f"Similitud A vs C (Distintos ejes): {similitud_coseno(vector_a, vector_c)}") # Debería ser 0.0
print("\n")


print("--- PRUEBA 2: SEMÁNTICA REAL (CON API GEMINI) ---")
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("⚠️ No encontré la variable GEMINI_API_KEY.")
    print("Para correr esta prueba, en tu terminal escribe primero:")
    print('$env:GEMINI_API_KEY="TU_LLAVE_AQUI"')
    print("Y luego vuelve a ejecutar este script.")
else:
    print("Llave encontrada. Conectando con Gemini...")
    embedder = GeminiEmbedder()
    
    frase1 = "Los gatos son animales adorables"
    frase2 = "Adoro a los felinos"
    frase3 = "La base de datos relacional utiliza SQL"
    
    print("Vectorizando textos...")
    vec1 = embedder.encode(frase1)
    vec2 = embedder.encode(frase2)
    vec3 = embedder.encode(frase3)
    
    # La frase 1 y 2 deberían tener un puntaje alto (cerca de 0.8 o más)
    print(f"[{frase1}] vs [{frase2}]")
    print(f"Similitud: {similitud_coseno(vec1, vec2):.4f}")
    
    # La frase 1 y 3 no tienen NADA que ver, deberían estar cerca de 0.0
    print(f"\n[{frase1}] vs [{frase3}]")
    print(f"Similitud: {similitud_coseno(vec1, vec3):.4f}")
