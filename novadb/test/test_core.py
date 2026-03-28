import unittest
import numpy as np
from novadb.core.node import Node
from novadb.core.graph import NovaGraph
from novadb.core.search import HierarchicalSearch

class TestNovaDBCore(unittest.TestCase):
    def setUp(self):
        self.graph = NovaGraph()
        
        # Vectores mock (matemáticamente predecibles para testing)
        self.v_gato = np.array([1.0, 0.0, 0.0])
        self.v_perro = np.array([0.9, 0.1, 0.0])
        self.v_auto = np.array([0.0, 1.0, 0.0])
        self.v_concept_animal = np.array([0.95, 0.05, 0.0])
        
    def test_insercion_y_vecindad(self):
        n1 = Node(text="Gato", vector=self.v_gato, tipo="MEMORIA")
        n2 = Node(text="Perro", vector=self.v_perro, tipo="MEMORIA")
        n3 = Node(text="Auto", vector=self.v_auto, tipo="MEMORIA")
        
        self.graph.insert(n1)
        self.graph.insert(n2)
        
        # n1 y n2 deberian agruparse como vecinos (similitud > 0.65)
        self.assertIn(n2.id, n1.vecinos)
        self.assertIn(n1.id, n2.vecinos)
        
        self.graph.insert(n3)
        # n3 no debería ser vecino de los animales (similitud 0.0)
        self.assertNotIn(n3.id, n1.vecinos)
        
    def test_insercion_jerarquica(self):
        # Insertamos concepto general primero
        n_macro = Node(text="Animales", vector=self.v_concept_animal, tipo="MACRO")
        self.graph.insert(n_macro)
        
        # Y luego uno especifico que debería enrutarse a ese macro (similitud alta)
        n_mem = Node(text="Gato", vector=self.v_gato, tipo="MEMORIA")
        self.graph.insert(n_mem)
        
        # Comprobaciones de paternidad
        self.assertIn(n_macro.id, n_mem.padres)
        self.assertIn(n_mem.id, n_macro.hijos)
        
    def test_busqueda_jerarquica(self):
        searcher = HierarchicalSearch(self.graph)
        
        # Poblamos grafo (Nota: Al insertarlos, se va a autoconectar mágicamente)
        n_macro = Node(text="Animales", vector=self.v_concept_animal, tipo="MACRO")
        n_mem1 = Node(text="Gato", vector=self.v_gato, tipo="MEMORIA")
        n_mem2 = Node(text="Perro", vector=self.v_perro, tipo="MEMORIA")
        n_otro = Node(text="Auto", vector=self.v_auto, tipo="MEMORIA")
        
        self.graph.insert(n_macro)
        self.graph.insert(n_mem1)
        self.graph.insert(n_mem2)
        self.graph.insert(n_otro)
        
        # Buscamos un animal usando un vector muy parecido a perro/gato
        query_vector = np.array([0.92, 0.08, 0.0])
        resultados = searcher.search(query_vector, top_k=2)
        
        # Recuperamos solo el texto de los resultados
        textos = [r[0].text for r in resultados]
        
        self.assertEqual(len(textos), 2)
        self.assertIn("Gato", textos)
        self.assertIn("Perro", textos)
        self.assertNotIn("Auto", textos)

if __name__ == '__main__':
    unittest.main()
