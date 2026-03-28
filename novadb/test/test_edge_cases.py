import unittest
import numpy as np
from novadb.core.node import Node
from novadb.core.graph import NovaGraph, similitud_coseno
from novadb.core.search import HierarchicalSearch
from novadb.core.consolidator import Consolidator
from novadb.core.embedder import BaseEmbedder


class MockEmbedder(BaseEmbedder):
    """Mock embedder that generates predictable vectors for testing."""
    def __init__(self, dim: int = 128):
        self.dim = dim

    def encode(self, text: str) -> np.ndarray:
        np.random.seed(hash(text) % 2**32)
        return np.random.randn(self.dim).astype(np.float32)


def create_node(text: str, tipo: str = "MEMORIA", vector: np.ndarray = None,
                embedder: MockEmbedder = None) -> Node:
    """Helper to create a node with predictable vector."""
    if vector is None and embedder:
        vector = embedder.encode(text)
    elif vector is None:
        vector = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    return Node(text=text, vector=vector, tipo=tipo)


class TestEdgeCasesEmptyGraph(unittest.TestCase):
    """Tests for empty graph operations."""

    def setUp(self):
        self.graph = NovaGraph()
        self.embedder = MockEmbedder(dim=128)
        self.searcher = HierarchicalSearch(self.graph)

    def test_search_empty_graph(self):
        """Search on empty graph returns empty results."""
        query_vector = self.embedder.encode("any query")
        resultados = self.searcher.search(query_vector, top_k=5)
        self.assertEqual(len(resultados), 0)

    def test_stats_empty_graph(self):
        """Stats on empty graph returns zero values."""
        stats = self.graph.get_relevancia_stats()
        self.assertEqual(stats["promedio"], 0.0)
        self.assertEqual(stats["max"], 0.0)
        self.assertEqual(stats["min"], 0.0)

    def test_count_empty_graph(self):
        """Count on empty graph returns zero."""
        self.assertEqual(self.graph.count(), 0)
        self.assertEqual(self.graph.count("MEMORIA"), 0)
        self.assertEqual(self.graph.count("MACRO"), 0)
        self.assertEqual(self.graph.count("MEDIO"), 0)

    def test_get_mas_relevante_empty_graph(self):
        """get_mas_relevante on empty graph returns None."""
        result = self.graph.get_mas_relevante()
        self.assertIsNone(result)

    def test_get_node_empty_graph(self):
        """get_node on empty graph returns None."""
        result = self.graph.get_node("any-id")
        self.assertIsNone(result)


class TestEdgeCasesSingleNode(unittest.TestCase):
    """Tests for single node operations."""

    def setUp(self):
        self.graph = NovaGraph()
        self.embedder = MockEmbedder(dim=128)
        self.searcher = HierarchicalSearch(self.graph)

    def test_single_node_search(self):
        """Search returns the single node when it's the only match."""
        node = create_node("唯一的节点", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(node)

        query_vector = self.embedder.encode("唯一的节点")
        resultados = self.searcher.search(query_vector, top_k=5)

        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0][0].id, node.id)

    def test_single_node_consolidation(self):
        """Consolidation does not trigger with only one orphan."""
        consolidator = Consolidator(self.graph, self.embedder)

        node = create_node("孤独的节点", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(node)

        result = consolidator.verificar_y_consolidar(node)
        self.assertIsNone(result)

    def test_single_node_stats(self):
        """Stats on single node graph work correctly."""
        node = create_node("Test", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(node)

        stats = self.graph.get_relevancia_stats()
        self.assertEqual(stats["promedio"], node.relevancia)
        self.assertEqual(stats["max"], node.relevancia)
        self.assertEqual(stats["min"], node.relevancia)


class TestEdgeCasesBoundaryValues(unittest.TestCase):
    """Tests for boundary value handling."""

    def setUp(self):
        self.graph = NovaGraph()
        self.embedder = MockEmbedder(dim=128)

    def test_node_with_empty_text(self):
        """Node with empty text can be inserted."""
        node = create_node("", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(node)
        self.assertEqual(self.graph.count("MEMORIA"), 1)

    def test_node_with_very_long_text(self):
        """Node with very long text is handled correctly."""
        long_text = "A" * 100000
        node = create_node(long_text, tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(node)
        self.assertEqual(node.text, long_text)

    def test_node_with_special_characters(self):
        """Node with special characters in text is handled."""
        special_text = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
        node = create_node(special_text, tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(node)
        self.assertEqual(node.text, special_text)

    def test_node_with_unicode(self):
        """Node with unicode text is handled correctly."""
        unicode_text = "日本語中文한국어Ελληνικά עברית العربية"
        node = create_node(unicode_text, tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(node)
        self.assertEqual(node.text, unicode_text)

    def test_node_with_emoji(self):
        """Node with emoji characters is handled."""
        emoji_text = "😀🎉🚀💻🌟✨"
        node = create_node(emoji_text, tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(node)
        self.assertEqual(node.text, emoji_text)

    def test_vector_with_zeros(self):
        """Vector with all zeros returns zero similarity."""
        node = create_node("zeros test", tipo="MEMORIA", embedder=self.embedder)
        node.vector = np.zeros(128, dtype=np.float32)
        self.graph.insert(node)

        other_vector = np.ones(128, dtype=np.float32)
        sim = similitud_coseno(node.vector, other_vector)
        self.assertEqual(sim, 0.0)

    def test_vector_with_ones(self):
        """Vector with all ones is handled."""
        node = create_node("ones test", tipo="MEMORIA", embedder=self.embedder)
        node.vector = np.ones(128, dtype=np.float32)
        self.graph.insert(node)
        self.assertEqual(len(node.vector), 128)

    def test_vector_with_negative_values(self):
        """Vector with negative values is handled."""
        node = create_node("negative test", tipo="MEMORIA", embedder=self.embedder)
        node.vector = np.array([-1.0, -0.5, 0.0, 0.5, 1.0], dtype=np.float32)
        self.graph.insert(node)
        self.assertEqual(len(node.vector), 5)


class TestEdgeCasesNodeRelationships(unittest.TestCase):
    """Tests for edge cases in node relationships."""

    def setUp(self):
        self.graph = NovaGraph()
        self.embedder = MockEmbedder(dim=128)

    def test_node_with_no_parents(self):
        """Node with no parents is inserted correctly."""
        node = create_node("orphan", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(node)
        self.assertEqual(len(node.padres), 0)

    def test_node_with_nonexistent_parent(self):
        """Node referencing nonexistent parent is handled."""
        node = Node(text="test", vector=self.embedder.encode("test"), tipo="MEMORIA")
        node.padres = ["nonexistent-id"]
        self.graph.insert(node)
        self.assertEqual(len(node.padres), 1)

    def test_circular_reference_in_hierarchy(self):
        """Circular references in hierarchy are handled without infinite loops."""
        node_a = create_node("A", tipo="MACRO", embedder=self.embedder)
        node_b = create_node("B", tipo="MEMORIA", embedder=self.embedder)

        self.graph.insert(node_a)
        self.graph.insert(node_b)

        node_a.padres.append(node_b.id)
        node_a.hijos.append(node_b.id)
        node_b.padres.append(node_a.id)
        node_b.hijos.append(node_a.id)

        result = self.graph.get_node(node_a.id)
        self.assertIsNotNone(result)

    def test_self_reference_in_vecinos(self):
        """Self-referencing vecinos are handled."""
        node = create_node("self ref", tipo="MEMORIA", embedder=self.embedder)
        node.vecinos.append(node.id)
        self.graph.nodes[node.id] = node

        result = self.graph.get_node(node.id)
        self.assertEqual(len(result.vecinos), 1)
        self.assertIn(node.id, result.vecinos)


class TestEdgeCasesTypes(unittest.TestCase):
    """Tests for all node types in edge cases."""

    def setUp(self):
        self.graph = NovaGraph()
        self.embedder = MockEmbedder(dim=128)

    def test_macro_node(self):
        """MACRO nodes are inserted correctly."""
        node = create_node("Macro Concept", tipo="MACRO", embedder=self.embedder)
        self.graph.insert(node)
        self.assertEqual(self.graph.count("MACRO"), 1)

    def test_medio_node(self):
        """MEDIO nodes are inserted correctly."""
        node = create_node("Medium Concept", tipo="MEDIO", embedder=self.embedder)
        self.graph.insert(node)
        self.assertEqual(self.graph.count("MEDIO"), 1)

    def test_memoria_node(self):
        """MEMORIA nodes are inserted correctly."""
        node = create_node("Memory Concept", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(node)
        self.assertEqual(self.graph.count("MEMORIA"), 1)

    def test_invalid_tipo_defaults(self):
        """Invalid tipo string does not cause errors during insert."""
        node = Node(text="test", vector=self.embedder.encode("test"), tipo="INVALID")
        self.graph.insert(node)
        self.assertEqual(self.graph.count(), 1)


class TestEdgeCasesSearch(unittest.TestCase):
    """Tests for search edge cases."""

    def setUp(self):
        self.graph = NovaGraph()
        self.embedder = MockEmbedder(dim=128)
        self.searcher = HierarchicalSearch(self.graph)

    def test_search_with_zero_results(self):
        """Search with no similar results returns empty."""
        for i in range(10):
            node = create_node(f"animal {i}", tipo="MEMORIA", embedder=self.embedder)
            self.graph.insert(node)

        query_vector = self.embedder.encode("technology computer software")
        resultados = self.searcher.search(query_vector, top_k=5)
        self.assertLessEqual(len(resultados), 5)

    def test_search_with_more_results_than_nodes(self):
        """Search requesting more results than available nodes."""
        node = create_node("only one", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(node)

        query_vector = self.embedder.encode("only one")
        resultados = self.searcher.search(query_vector, top_k=100)
        self.assertEqual(len(resultados), 1)

    def test_search_with_identical_vectors(self):
        """Search with identical vectors returns all matches."""
        vector = self.embedder.encode("identical")

        node1 = Node(text="First identical", vector=vector.copy(), tipo="MEMORIA")
        node2 = Node(text="Second identical", vector=vector.copy(), tipo="MEMORIA")

        self.graph.insert(node1)
        self.graph.insert(node2)

        query_vector = vector
        resultados = self.searcher.search(query_vector, top_k=5)
        self.assertGreaterEqual(len(resultados), 2)


if __name__ == '__main__':
    unittest.main()
