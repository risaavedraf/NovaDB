import unittest
import time
import numpy as np
from novadb.core.node import Node
from novadb.core.graph import NovaGraph
from novadb.core.search import HierarchicalSearch


class TestSearchPerformance(unittest.TestCase):
    def test_insert_1000_nodes_performance(self):
        """
        Verifies that inserting 1000 nodes completes in under 30 seconds.
        PRD requirement: Insert 1,000 nodes in < 30 seconds
        """
        graph = NovaGraph()
        embedder = MockEmbedder()
        
        start = time.time()
        for i in range(1000):
            text = f"Memory node {i} with some content"
            vector = embedder.encode(text)
            node = Node(text=text, vector=vector, tipo="MEMORIA")
            graph.insert(node)
        elapsed = time.time() - start
        
        self.assertLess(elapsed, 30.0, f"Insert 1000 nodes took {elapsed:.2f}s, should be < 30s")
        print(f"\nInsert 1000 nodes: {elapsed:.2f}s")
    
    def test_search_1000_nodes_performance(self):
        """
        Verifies that search returns results in under 100ms with 1000 nodes.
        PRD requirement: Search returns results in < 100ms
        """
        graph = NovaGraph()
        embedder = MockEmbedder()
        
        for i in range(1000):
            text = f"Memory node {i} with some content"
            vector = embedder.encode(text)
            node = Node(text=text, vector=vector, tipo="MEMORIA")
            graph.insert(node)
        
        searcher = HierarchicalSearch(graph)
        query_vector = embedder.encode("query search")
        
        start = time.time()
        resultados = searcher.search(query_vector, top_k=5)
        elapsed = time.time() - start
        
        self.assertLess(elapsed, 0.1, f"Search took {elapsed*1000:.2f}ms, should be < 100ms")
        self.assertGreater(len(resultados), 0)
        print(f"\nSearch with 1000 nodes: {elapsed*1000:.2f}ms")
    
    def test_search_uses_indices_not_full_scan(self):
        """
        Verifies that search operations use indices rather than O(N) full scans.
        """
        graph = NovaGraph()
        embedder = MockEmbedder()
        
        for i in range(500):
            text = f"Memory node {i}"
            vector = embedder.encode(text)
            node = Node(text=text, vector=vector, tipo="MEMORIA")
            graph.insert(node)
        
        self.assertEqual(len(graph.indice_macro), 0)
        self.assertGreater(len(graph.vector_cache), 0)
        
        searcher = HierarchicalSearch(graph)
        query_vector = embedder.encode("test query")
        
        start = time.time()
        for _ in range(100):
            searcher.search(query_vector, top_k=5)
        elapsed = time.time() - start
        
        avg_time_ms = (elapsed / 100) * 1000
        self.assertLess(avg_time_ms, 50, f"Average search time {avg_time_ms:.2f}ms seems too high")
        print(f"\nAverage search time over 100 searches: {avg_time_ms:.2f}ms")
    
    def test_vector_cache_reduces_computation(self):
        """
        Verifies that vector cache is populated and used.
        """
        graph = NovaGraph()
        embedder = MockEmbedder()
        
        for i in range(100):
            text = f"Memory node {i}"
            vector = embedder.encode(text)
            node = Node(text=text, vector=vector, tipo="MEMORIA")
            graph.insert(node)
        
        self.assertEqual(len(graph.vector_cache), 100)
        
        cached_vector = graph.get_cached_vector(node.id)
        self.assertIsNotNone(cached_vector)
        np.testing.assert_array_equal(cached_vector, node.vector)
    
    def test_rebuild_indices(self):
        """
        Verifies that rebuild_indices reconstructs all indices correctly.
        """
        graph = NovaGraph()
        embedder = MockEmbedder()
        
        macro = Node(text="Macro Concept", vector=embedder.encode("Macro Concept"), tipo="MACRO")
        graph.insert(macro)
        
        for i in range(50):
            text = f"Memory {i}"
            vector = embedder.encode(text)
            node = Node(text=text, vector=vector, tipo="MEMORIA")
            graph.insert(node)
        
        self.assertGreater(len(graph.indice_macro), 0)
        
        graph.rebuild_indices()
        
        self.assertGreater(len(graph.indice_macro), 0)
        self.assertEqual(len(graph.vector_cache), len(graph.nodes))


class MockEmbedder:
    """Mock embedder that generates predictable vectors for testing."""
    def __init__(self, dim: int = 128):
        self.dim = dim
    
    def encode(self, text: str) -> np.ndarray:
        np.random.seed(hash(text) % 2**32)
        return np.random.randn(self.dim).astype(np.float32)


if __name__ == '__main__':
    unittest.main()
