import unittest
import numpy as np
from novadb.core.node import Node
from novadb.core.graph import NovaGraph
from novadb.core.consolidator import Consolidator

# Mock Embedder para no depender de API en los tests unitarios
class MockEmbedder:
    def encode(self, text: str):
        # Devolver vector de dim 3 para que coincida con los vectores dummy de los tests
        return np.array([1.0, 0.0, 0.0], dtype=np.float32)

def mock_llm_namer(textos):
    return "Concepto Automatizado"

class TestConsolidador(unittest.TestCase):
    def setUp(self):
        self.graph = NovaGraph()
        self.embedder = MockEmbedder()
        self.consolidator = Consolidator(
            graph=self.graph, 
            embedder=self.embedder, 
            umbral_consolidacion=0.75,
            llm_namer=mock_llm_namer
        )
        
    def test_threshold_dinamico(self):
        # Sin memorias -> threshold min = 3
        self.assertEqual(self.consolidator.threshold_optimo(), 3)
        
        # Simulamos un volumen mediano (100 memorias libres)
        for i in range(100):
            n = Node(text=f"test {i}", vector=np.random.rand(3), tipo="MEMORIA")
            self.graph.nodes[n.id] = n
            
        # 1 Nodo medio -> grupo ideal = sqrt(100)/1 = 10
        self.graph.nodes["medio_falso"] = Node(text="un medio", vector=np.random.rand(3), tipo="MEDIO")
        self.assertEqual(self.consolidator.threshold_optimo(), 10)
        
    def test_consolidacion_automatica_hook(self):
        # Insertamos un MACRO primero para probar que el fallback no rompe el consolidador
        macro = Node(text="Concepto Padre Macro", vector=np.array([1.0, 0.0, 0.0]), tipo="MACRO")
        self.graph.insert(macro)
        
        # Matrices identicas para asegurar similitud (se anclaran al MACRO por fallback)
        v_comun = np.array([0.9, 0.1, 0.0])
        n1 = Node(text="Dato 1", vector=v_comun, tipo="MEMORIA")
        n2 = Node(text="Dato 2", vector=v_comun, tipo="MEMORIA")
        
        self.graph.insert(n1)
        self.graph.insert(n2)
        
        # Con 2 nodos no debe consolidar (min=3)
        self.assertIsNone(self.consolidator.verificar_y_consolidar(n2))
        
        n3 = Node(text="Dato 3", vector=v_comun, tipo="MEMORIA")
        self.graph.insert(n3)
        
        # Con el 3ro se alcanza masa critica, disparamos
        nuevo_medio = self.consolidator.verificar_y_consolidar(n3)
        
        # Verificamos eclosión
        self.assertIsNotNone(nuevo_medio)
        self.assertEqual(nuevo_medio.tipo, "MEDIO")
        self.assertEqual(nuevo_medio.text, "Concepto Automatizado")
        
        # Verificamos reorganización del grafo (la magia autogestionada)
        self.assertIn(nuevo_medio.id, n1.padres)
        self.assertIn(nuevo_medio.id, n2.padres)
        self.assertIn(nuevo_medio.id, n3.padres)
        self.assertEqual(len(nuevo_medio.hijos), 3)

    def test_consolidacion_offline(self):
        """Verifica que la consolidación funciona SIN LLM (naming offline)."""
        consolidator = Consolidator(
            graph=self.graph,
            embedder=self.embedder,
            umbral_consolidacion=0.75,
            llm_namer=None  # Sin LLM
        )

        v_comun = np.array([0.5, 0.5, 0.0])
        n1 = Node(text="Python machine learning algorithm", vector=v_comun, tipo="MEMORIA")
        n2 = Node(text="Python deep learning neural network", vector=v_comun, tipo="MEMORIA")
        n3 = Node(text="Python data science analysis", vector=v_comun, tipo="MEMORIA")

        self.graph.insert(n1)
        self.graph.insert(n2)
        self.graph.insert(n3)

        nuevo_medio = consolidator.verificar_y_consolidar(n3)
        self.assertIsNotNone(nuevo_medio)
        self.assertEqual(nuevo_medio.tipo, "MEDIO")
        self.assertEqual(nuevo_medio.metadata["naming_mode"], "offline")
        # "Python" debería aparecer en el nombre por ser la keyword más frecuente
        self.assertIn("Python", nuevo_medio.text)

    def test_consolidacion_offline_fallback(self):
        """Verifica que el fallback genera nombre cuando los stopwords dominan."""
        nombre = self.consolidator._nombrar_grupo_offline(["el la de un", "la de en el"])
        self.assertTrue(nombre.startswith("Untitled Group"))

if __name__ == '__main__':
    unittest.main()
