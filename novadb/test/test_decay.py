import unittest
import math
import time
import numpy as np
from datetime import datetime, timedelta
from novadb.core.node import Node
from novadb.core.graph import NovaGraph, DECAY_RATE_DEFAULT, RELEVANCIA_WEIGHT_DEFAULT
from novadb.core.search import HierarchicalSearch


class TestDecay(unittest.TestCase):
    def setUp(self):
        self.graph = NovaGraph(decay_rate=0.1, relevancia_weight=0.3)
        self.v_gato = np.array([1.0, 0.0, 0.0])
        self.v_perro = np.array([0.9, 0.1, 0.0])
        self.v_auto = np.array([0.0, 1.0, 0.0])
        self.v_concept_animal = np.array([0.95, 0.05, 0.0])

    def test_nodo_nuevo_tiene_relevancia_inicial(self):
        nodo = Node(text="Test", vector=self.v_gato, tipo="MEMORIA")
        self.assertEqual(nodo.relevancia, 0.5)
        self.assertEqual(nodo.accesos, 0)

    def test_relevancia_aumenta_con_acceso(self):
        nodo = Node(text="Test", vector=self.v_gato, tipo="MEMORIA")
        self.graph.nodes[nodo.id] = nodo
        
        initial_relevancia = nodo.relevancia
        self.graph.update_relevancia_on_access(nodo)
        
        self.assertGreater(nodo.relevancia, initial_relevancia)
        self.assertEqual(nodo.accesos, 1)

    def test_relevancia_boost_hacia_1_con_accesos_multiples(self):
        nodo = Node(text="Test", vector=self.v_gato, tipo="MEMORIA", relevancia=0.5)
        self.graph.nodes[nodo.id] = nodo
        
        for _ in range(10):
            self.graph.update_relevancia_on_access(nodo)
        
        self.assertGreater(nodo.relevancia, 0.9)
        self.assertEqual(nodo.accesos, 10)

    def test_relevancia_decae_over_time(self):
        nodo = Node(text="Test", vector=self.v_gato, tipo="MEMORIA", relevancia=0.8)
        nodo.updated_at = datetime.now() - timedelta(hours=10)
        self.graph.nodes[nodo.id] = nodo
        
        self.graph.apply_temporal_decay()
        
        self.assertLess(nodo.relevancia, 0.8)
        self.assertGreater(nodo.relevancia, 0.0)

    def test_decay_exponencial_calculo_correcto(self):
        decay_rate = 0.1
        graph = NovaGraph(decay_rate=decay_rate)
        
        nodo = Node(text="Test", vector=self.v_gato, tipo="MEMORIA", relevancia=1.0)
        nodo.updated_at = datetime.now() - timedelta(hours=10)
        graph.nodes[nodo.id] = nodo
        
        graph.apply_temporal_decay()
        
        expected = 1.0 * math.exp(-decay_rate * 10)
        self.assertAlmostEqual(nodo.relevancia, expected, places=5)

    def test_get_node_no_mutate_relevancia(self):
        """get_node() is a pure read — no side effects on relevancia or accesos."""
        nodo = Node(text="Test", vector=self.v_gato, tipo="MEMORIA", relevancia=0.5)
        self.graph.nodes[nodo.id] = nodo
        
        retrieved = self.graph.get_node(nodo.id)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.relevancia, 0.5)
        self.assertEqual(retrieved.accesos, 0)

    def test_update_relevancia_on_access_boosts(self):
        """update_relevancia_on_access() explicitly boosts relevancia."""
        nodo = Node(text="Test", vector=self.v_gato, tipo="MEMORIA", relevancia=0.5)
        self.graph.nodes[nodo.id] = nodo
        
        self.graph.update_relevancia_on_access(nodo)
        
        self.assertGreater(nodo.relevancia, 0.5)
        self.assertEqual(nodo.accesos, 1)

    def test_combined_score_mezcla_similitud_y_relevancia(self):
        cosine_sim = 0.9
        nodo = Node(text="Test", vector=self.v_gato, tipo="MEMORIA", relevancia=0.8)
        
        score = self.graph.calculate_combined_score(cosine_sim, nodo)
        
        expected = (cosine_sim * 0.7) + (0.8 * 0.3)
        self.assertAlmostEqual(score, expected)

    def test_relevancia_stats(self):
        n1 = Node(text="N1", vector=self.v_gato, tipo="MEMORIA", relevancia=0.3)
        n2 = Node(text="N2", vector=self.v_perro, tipo="MEMORIA", relevancia=0.7)
        n3 = Node(text="N3", vector=self.v_auto, tipo="MEMORIA", relevancia=0.5)
        
        self.graph.nodes[n1.id] = n1
        self.graph.nodes[n2.id] = n2
        self.graph.nodes[n3.id] = n3
        
        stats = self.graph.get_relevancia_stats()
        
        self.assertAlmostEqual(stats["promedio"], (0.3 + 0.7 + 0.5) / 3)
        self.assertEqual(stats["max"], 0.7)
        self.assertEqual(stats["min"], 0.3)

    def test_nodo_mas_relevante(self):
        n1 = Node(text="N1", vector=self.v_gato, tipo="MEMORIA", relevancia=0.3)
        n2 = Node(text="N2", vector=self.v_perro, tipo="MEMORIA", relevancia=0.9)
        
        self.graph.nodes[n1.id] = n1
        self.graph.nodes[n2.id] = n2
        
        mas_relevante, score = self.graph.get_mas_relevante()
        
        self.assertEqual(mas_relevante.text, "N2")
        self.assertEqual(score, 0.9)

    def test_search_mezcla_relevancia_en_ranking(self):
        n_macro = Node(text="Animales", vector=self.v_concept_animal, tipo="MACRO")
        n_mem1 = Node(text="Gato", vector=self.v_gato, tipo="MEMORIA", relevancia=0.2)
        n_mem2 = Node(text="Perro", vector=self.v_perro, tipo="MEMORIA", relevancia=0.9)
        
        self.graph.nodes[n_macro.id] = n_macro
        self.graph.nodes[n_mem1.id] = n_mem1
        self.graph.nodes[n_mem2.id] = n_mem2
        
        self.graph.insert(n_mem1)
        self.graph.insert(n_mem2)
        
        searcher = HierarchicalSearch(self.graph)
        query_vector = np.array([0.92, 0.08, 0.0])
        resultados = searcher.search(query_vector, top_k=2)
        
        textos = [r[0].text for r in resultados]
        self.assertIn("Perro", textos)
        self.assertIn("Gato", textos)
        
        nodo_perro = next(n for n, s in resultados if n.text == "Perro")
        self.assertGreater(nodo_perro.relevancia, 0.9)

    def test_nodos_sin_acceso_tienen_decay(self):
        nodo = Node(text="Test", vector=self.v_gato, tipo="MEMORIA", relevancia=0.8)
        nodo.updated_at = datetime.now() - timedelta(hours=5)
        self.graph.nodes[nodo.id] = nodo
        
        self.graph.apply_temporal_decay()
        
        expected = 0.8 * math.exp(-self.graph.decay_rate * 5)
        self.assertAlmostEqual(nodo.relevancia, expected, places=5)

    def test_nodos_ningun_vector_no_son_afectados(self):
        nodo = Node(text="Test", vector=self.v_gato, tipo="MEMORIA", relevancia=0.8)
        nodo.vector = None
        nodo.updated_at = datetime.now() - timedelta(hours=100)
        self.graph.nodes[nodo.id] = nodo
        
        original = nodo.relevancia
        self.graph.apply_temporal_decay()
        
        self.assertEqual(nodo.relevancia, original)

    def test_persistencia_relevancia_en_to_dict(self):
        nodo = Node(text="Test", vector=self.v_gato, tipo="MEMORIA", relevancia=0.75, accesos=5)
        
        data = nodo.to_dict()
        
        self.assertEqual(data["relevancia"], 0.75)
        self.assertEqual(data["accesos"], 5)

    def test_persistencia_relevancia_en_from_dict(self):
        data = {
            "id": "test-id",
            "text": "Test",
            "vector": [1.0, 0.0, 0.0],
            "tipo": "MEMORIA",
            "metadata": {},
            "padres": [],
            "hijos": [],
            "vecinos": [],
            "conexiones": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "accesos": 10,
            "relevancia": 0.88
        }
        
        nodo = Node.from_dict(data)
        
        self.assertEqual(nodo.relevancia, 0.88)
        self.assertEqual(nodo.accesos, 10)

    def test_graph_configuracion_decay(self):
        graph = NovaGraph(decay_rate=0.05, relevancia_weight=0.4)
        
        self.assertEqual(graph.decay_rate, 0.05)
        self.assertEqual(graph.relevancia_weight, 0.4)


class TestDecayIntegration(unittest.TestCase):
    def setUp(self):
        self.graph = NovaGraph(k_vecinos=3, decay_rate=0.01, relevancia_weight=0.3)
        self.v1 = np.array([1.0, 0.0, 0.0])
        self.v2 = np.array([0.0, 1.0, 0.0])

    def test_acceso_multiple_a_mismo_nodo_incrementa_relevancia(self):
        nodo = Node(text="Test", vector=self.v1, tipo="MEMORIA", relevancia=0.5)
        self.graph.nodes[nodo.id] = nodo
        
        for _ in range(5):
            self.graph.update_relevancia_on_access(nodo)
        
        self.assertGreater(nodo.relevancia, 0.95)
        self.assertEqual(nodo.accesos, 5)

    def test_decay_factor_default(self):
        self.assertEqual(DECAY_RATE_DEFAULT, 0.0001)
        self.assertEqual(RELEVANCIA_WEIGHT_DEFAULT, 0.3)


if __name__ == '__main__':
    unittest.main()
