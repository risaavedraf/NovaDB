import os
import unittest
import numpy as np
from novadb.novadb import NovaDB
from novadb.core.embedder import BaseEmbedder

# Mock Embedder para la demo E2E, genera vectores estables localmente
class MockE2EEmbedder(BaseEmbedder):
    def encode(self, text: str):
        # Semantica de juguete: Textos de longitudes similares estaran "cerca"
        val = float(len(text) % 10) / 10.0
        return np.array([val, 1.0 - val, 0.5], dtype=np.float32)

class TestNovaDBE2E(unittest.TestCase):
    def setUp(self):
        self.db_path = "e2e_test_db.msgpack"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
        self.db = NovaDB(embedder=MockE2EEmbedder(), path=self.db_path, autosave=True)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_flujo_completo(self):
        # 1. Inserción de Estructura MACRO (Ej: Un PRD)
        id_macro = self.db.insert("NovaDB PRD", tipo="MACRO", metadata={"source": "NovaDB_PRD.md"})
        
        # 2. Inserción de Nodos MEMORIA (Hechos aislados)
        self.db.insert("El autobalanceo de jerarquia se basa en raiz cuadrada.")
        self.db.insert("La persistencia ocupa MessagePack por su eficiencia en prod.")
        id_concepto = self.db.insert("El sub-agente Némesis tiene rol de auditor frio.")
        
        # 3. Verificamos estadisticas O(1)
        stats = self.db.stats()
        self.assertEqual(stats["total_nodos"], 4)
        self.assertEqual(stats["por_tipo"]["MACRO"], 1)
        self.assertEqual(stats["por_tipo"]["MEMORIA"], 3)
        
        # 4. Busqueda Semantica (el Mock embedder encontrara los de largo similar)
        resultados = self.db.search("persist", n=2)
        self.assertTrue(len(resultados) > 0)
        
        # 5. Persistencia automatica (autosave=True deberia haber guardado el archivo)
        self.assertTrue(os.path.exists(self.db_path))
        
        # 6. Reanimación del cerebro en otra instancia independiente
        db_clon = NovaDB(embedder=MockE2EEmbedder(), path=self.db_path)
        stats_clon = db_clon.stats()
        self.assertEqual(stats_clon["total_nodos"], 4)
        
        # 7. Relacionales e introspeccion directa (Node -> Metadata)
        nodo_recuperado = db_clon.get(id_concepto)
        self.assertIsNotNone(nodo_recuperado)
        self.assertEqual(nodo_recuperado.tipo, "MEMORIA")

if __name__ == '__main__':
    unittest.main()
