import unittest
import tempfile
import os
import shutil
import numpy as np
from novadb.core.node import Node
from novadb.core.graph import NovaGraph
from novadb.core.search import HierarchicalSearch
from novadb.core.consolidator import Consolidator
from novadb.novadb import NovaDB
from novadb.storage import disk
from novadb.storage import exporter
from novadb.core.embedder import BaseEmbedder


class MockEmbedder(BaseEmbedder):
    """Mock embedder that generates predictable vectors for testing."""
    def __init__(self, dim: int = 128):
        self.dim = dim

    def encode(self, text: str) -> np.ndarray:
        np.random.seed(hash(text) % 2**32)
        return np.random.randn(self.dim).astype(np.float32)


class MockGeminiClient:
    """Mock client for bypassing API calls — kept for reference but unused."""
    pass


def mock_llm_namer(textos):
    return "Concepto Automatizado"


def create_node(text: str, tipo: str = "MEMORIA", vector: np.ndarray = None,
                embedder: MockEmbedder = None) -> Node:
    """Helper to create a node with predictable vector."""
    if vector is None and embedder:
        vector = embedder.encode(text)
    elif vector is None:
        vector = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    return Node(text=text, vector=vector, tipo=tipo)


class MockE2EEmbedder(BaseEmbedder):
    """Mock embedder with predictable output for E2E tests."""
    def __init__(self, dim: int = 128):
        self.dim = dim

    def encode(self, text: str) -> np.ndarray:
        np.random.seed(hash(text) % 2**32)
        return np.random.randn(self.dim).astype(np.float32)


class TestFullWorkflows(unittest.TestCase):
    """Integration tests for complete workflows."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.embedder = MockE2EEmbedder(dim=128)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_workflow_insert_search_save_load(self):
        """Complete workflow: insert, search, save, load."""
        db_path = os.path.join(self.temp_dir, "workflow_test.msgpack")
        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)

        db.insert("First memory about animals", tipo="MEMORIA")
        db.insert("Second memory about dogs", tipo="MEMORIA")
        db.insert("Third memory about cats", tipo="MEMORIA")

        stats_before = db.stats()
        self.assertEqual(stats_before["total_nodos"], 3)

        results = db.search("dogs", n=2)
        self.assertGreaterEqual(len(results), 1)

        db.save(db_path)
        self.assertTrue(os.path.exists(db_path))

        db_loaded = NovaDB(embedder=self.embedder, path=db_path)

        stats_after = db_loaded.stats()
        self.assertEqual(stats_after["total_nodos"], 3)

    def test_full_workflow_with_consolidation(self):
        """Workflow with consolidation triggered."""
        db_path = os.path.join(self.temp_dir, "consolidation_test.msgpack")
        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)
        db.consolidator.llm_namer = mock_llm_namer

        for i in range(5):
            db.insert(f"memory fragment {i} about technology", tipo="MEMORIA")

        stats = db.stats()
        self.assertGreaterEqual(stats["total_nodos"], 5)

    def test_multiple_save_load_cycles(self):
        """Multiple save/load cycles preserve data integrity."""
        db_path = os.path.join(self.temp_dir, "cycles_test.msgpack")

        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)

        for i in range(10):
            db.insert(f"memory {i}", tipo="MEMORIA")

        for cycle in range(3):
            db.save()

            db_loaded = NovaDB(embedder=self.embedder, path=db_path)
    
            stats = db_loaded.stats()
            self.assertEqual(stats["total_nodos"], 10)

            db = db_loaded

    def test_concurrent_insert_simulation(self):
        """Simulates multiple inserts in sequence."""
        db_path = os.path.join(self.temp_dir, "concurrent_test.msgpack")
        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)

        texts = [
            "Python programming language",
            "JavaScript web development",
            "Machine learning algorithms",
            "Database management systems",
            "Network security protocols",
            "Cloud computing infrastructure",
            "Data structures and algorithms",
            "Software engineering practices",
            "Web application architecture",
            "Distributed systems design"
        ]

        for text in texts:
            db.insert(text, tipo="MEMORIA")

        stats = db.stats()
        self.assertEqual(stats["total_nodos"], len(texts))

        results = db.search("programming", n=3)
        self.assertGreaterEqual(len(results), 1)


class TestExportWorkflows(unittest.TestCase):
    """Tests for export functionality in workflows."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.embedder = MockE2EEmbedder(dim=128)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_md_creates_file(self):
        """Export to markdown creates a file."""
        db_path = os.path.join(self.temp_dir, "export_test.msgpack")
        md_path = os.path.join(self.temp_dir, "export.md")

        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)

        db.insert("First memory", tipo="MEMORIA")
        db.insert("Second memory", tipo="MEMORIA")

        db.export_md(md_path)

        self.assertTrue(os.path.exists(md_path))

    def test_export_md_content_structure(self):
        """Export markdown has correct structure."""
        db_path = os.path.join(self.temp_dir, "export_test.msgpack")
        md_path = os.path.join(self.temp_dir, "export.md")

        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)

        db.insert("Test memory", tipo="MEMORIA")

        db.export_md(md_path)

        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("NovaDB", content)
        self.assertIn("Test memory", content)

    def test_export_md_empty_graph(self):
        """Export empty graph creates file with headers."""
        md_path = os.path.join(self.temp_dir, "empty_export.md")

        graph = NovaGraph()
        exporter.export_to_markdown(graph, md_path)

        self.assertTrue(os.path.exists(md_path))

        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("NovaDB", content)

    def test_export_md_directory_creation(self):
        """Export creates directory if it doesn't exist."""
        nested_path = os.path.join(self.temp_dir, "nested", "deep", "export.md")

        db_path = os.path.join(self.temp_dir, "test.msgpack")
        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)

        db.insert("Memory", tipo="MEMORIA")

        db.export_md(nested_path)

        self.assertTrue(os.path.exists(nested_path))


class TestSearchIntegration(unittest.TestCase):
    """Integration tests for search functionality."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.embedder = MockE2EEmbedder(dim=128)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_search_returns_formatted_results(self):
        """Search returns properly formatted results."""
        db_path = os.path.join(self.temp_dir, "search_test.msgpack")
        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)

        db.insert("Python programming tutorial", tipo="MEMORIA")
        db.insert("JavaScript basics", tipo="MEMORIA")

        results = db.search("python", n=5)

        self.assertGreater(len(results), 0)
        for result in results:
            self.assertIn("text", result)
            self.assertIn("_score", result)
            self.assertNotIn("vector", result)

    def test_search_with_no_results(self):
        """Search handles no results gracefully."""
        db_path = os.path.join(self.temp_dir, "no_results_test.msgpack")
        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)

        db.insert("completely unrelated content", tipo="MEMORIA")

        results = db.search("xyz123 nonexistent query", n=5)

        self.assertIsInstance(results, list)

    def test_search_respects_n_parameter(self):
        """Search respects the n parameter."""
        db_path = os.path.join(self.temp_dir, "n_param_test.msgpack")
        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)

        for i in range(20):
            db.insert(f"memory content {i}", tipo="MEMORIA")

        results = db.search("memory", n=3)

        self.assertLessEqual(len(results), 3)


class TestGraphOperationsIntegration(unittest.TestCase):
    """Integration tests for graph operations."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.embedder = MockE2EEmbedder(dim=128)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_insert_with_metadata(self):
        """Insert with metadata preserves metadata."""
        db_path = os.path.join(self.temp_dir, "metadata_test.msgpack")
        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)

        node_id = db.insert(
            "Memory with metadata",
            tipo="MEMORIA",
            metadata={"source": "test", "priority": 1}
        )

        node = db.get(node_id)
        self.assertEqual(node.metadata.get("source"), "test")
        self.assertEqual(node.metadata.get("priority"), 1)

    def test_connect_two_nodes(self):
        """Connect creates proper relationship between nodes."""
        db_path = os.path.join(self.temp_dir, "connect_test.msgpack")
        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)

        id1 = db.insert("Node one", tipo="MEMORIA")
        id2 = db.insert("Node two", tipo="MEMORIA")

        db.connect(id1, id2, "related", peso=0.8)

        node1 = db.get(id1)
        self.assertEqual(len(node1.conexiones), 1)
        self.assertEqual(node1.conexiones[0]["target"], id2)
        self.assertEqual(node1.conexiones[0]["tipo"], "related")

    def test_connect_nonexistent_nodes_raises(self):
        """Connect with nonexistent nodes raises ValueError."""
        db_path = os.path.join(self.temp_dir, "connect_error_test.msgpack")
        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)

        with self.assertRaises(ValueError):
            db.connect("nonexistent1", "nonexistent2", "related")

    def test_stats_returns_complete_metrics(self):
        """Stats returns complete metrics as per PRD Section 8."""
        db_path = os.path.join(self.temp_dir, "stats_test.msgpack")
        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)

        db.insert("First", tipo="MACRO")
        db.insert("Second", tipo="MEMORIA")
        db.insert("Third", tipo="MEMORIA")

        stats = db.stats()

        prd_fields = [
            "total_nodos", "por_tipo", "nodos_huerfanos",
            "conexiones_totales", "promedio_vecinos", "nodo_mas_accedido",
            "ultima_consolidacion", "tamano_disco_mb",
            "threshold_actual", "grupo_ideal", "balance_ratio",
            "medio_sobrecargados", "medio_vacios", "rebalanceo_recomendado",
            "decay_rate", "relevancia_weight", "nodos_muy_relevantes",
            "nodos_desatendidos", "relevancia_promedio"
        ]
        for field in prd_fields:
            self.assertIn(field, stats, f"Missing PRD field: {field}")
        
        self.assertEqual(stats["total_nodos"], 3)
        self.assertEqual(stats["por_tipo"]["MACRO"], 1)
        self.assertEqual(stats["por_tipo"]["MEMORIA"], 2)
        self.assertIsInstance(stats["nodos_huerfanos"], int)
        self.assertIsInstance(stats["conexiones_totales"], int)
        self.assertIsInstance(stats["promedio_vecinos"], float)
        self.assertIsInstance(stats["nodo_mas_accedido"], dict)
        self.assertIsInstance(stats["tamano_disco_mb"], float)
        self.assertIsInstance(stats["rebalanceo_recomendado"], bool)
        self.assertIsInstance(stats["decay_rate"], float)
        self.assertIsInstance(stats["relevancia_weight"], float)
        self.assertIsInstance(stats["nodos_muy_relevantes"], int)
        self.assertIsInstance(stats["nodos_desatendidos"], int)
        self.assertIsInstance(stats["relevancia_promedio"], float)
        self.assertEqual(stats["ultima_consolidacion"], None)


class TestPersistencAndConsolidationIntegration(unittest.TestCase):
    """Integration tests for persistence with consolidation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.embedder = MockE2EEmbedder(dim=128)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_consolidation_survives_save_load(self):
        """Consolidated nodes persist through save/load."""
        db_path = os.path.join(self.temp_dir, "consolidation_persist.msgpack")

        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)
        db.consolidator.llm_namer = mock_llm_namer

        for i in range(5):
            db.insert(f"consolidation test {i} content", tipo="MEMORIA")

        medio_count_before = db.stats()["por_tipo"]["MEDIO"]

        db.save()

        db_loaded = NovaDB(embedder=self.embedder, path=db_path)
        db_loaded.consolidator.llm_namer = mock_llm_namer

        medio_count_after = db_loaded.stats()["por_tipo"]["MEDIO"]

        self.assertEqual(medio_count_before, medio_count_after)

    def test_stats_orphan_nodes(self):
        """Stats correctly counts orphan MEMORIA nodes (no MEDIO parent)."""
        db_path = os.path.join(self.temp_dir, "orphan_test.msgpack")
        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)

        db.insert("Orphan 1", tipo="MEMORIA")
        db.insert("Orphan 2", tipo="MEMORIA")
        db.insert("Orphan 3", tipo="MEMORIA")
        db.insert("With Medio", tipo="MACRO")
        
        medio_node = Node(
            text="Test Medio", 
            vector=self.embedder.encode("Test Medio"), 
            tipo="MEDIO"
        )
        db.graph.insert(medio_node)
        
        memorias = [n for n in db.graph.nodes.values() if n.tipo == "MEMORIA"]
        if memorias:
            memorias[0].padres.append(medio_node.id)
            medio_node.hijos.append(memorias[0].id)
        
        stats = db.stats()
        self.assertEqual(stats["nodos_huerfanos"], 2)
        self.assertEqual(stats["por_tipo"]["MEMORIA"], 3)

    def test_stats_nodo_mas_accedido(self):
        """Stats correctly identifies most accessed node."""
        db_path = os.path.join(self.temp_dir, "mas_accedido_test.msgpack")
        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)

        db.insert("Node A", tipo="MEMORIA")
        db.insert("Node B", tipo="MEMORIA")
        db.insert("Node C", tipo="MEMORIA")

        db.get(list(db.graph.nodes.keys())[0])
        db.get(list(db.graph.nodes.keys())[0])
        db.get(list(db.graph.nodes.keys())[1])

        stats = db.stats()
        self.assertIsNotNone(stats["nodo_mas_accedido"])
        self.assertEqual(stats["nodo_mas_accedido"]["accesos"], 2)

    def test_stats_empty_graph(self):
        """Stats handles empty graph gracefully."""
        db_path = os.path.join(self.temp_dir, "empty_stats_test.msgpack")
        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)

        stats = db.stats()
        
        self.assertEqual(stats["total_nodos"], 0)
        self.assertEqual(stats["por_tipo"]["MACRO"], 0)
        self.assertEqual(stats["por_tipo"]["MEDIO"], 0)
        self.assertEqual(stats["por_tipo"]["MEMORIA"], 0)
        self.assertEqual(stats["nodos_huerfanos"], 0)
        self.assertEqual(stats["conexiones_totales"], 0)
        self.assertEqual(stats["promedio_vecinos"], 0.0)
        self.assertIsNone(stats["nodo_mas_accedido"])
        self.assertEqual(stats["ultima_consolidacion"], None)
        self.assertEqual(stats["nodos_muy_relevantes"], 0)
        self.assertEqual(stats["nodos_desatendidos"], 0)

    def test_stats_single_node(self):
        """Stats handles single node graph."""
        db_path = os.path.join(self.temp_dir, "single_node_stats.msgpack")
        db = NovaDB(embedder=self.embedder, path=db_path, autosave=False)

        db.insert("Solo", tipo="MEMORIA")
        
        stats = db.stats()
        self.assertEqual(stats["total_nodos"], 1)
        self.assertEqual(stats["por_tipo"]["MEMORIA"], 1)
        self.assertIsNotNone(stats["nodo_mas_accedido"])
        self.assertEqual(stats["nodo_mas_accedido"]["text"], "Solo")


if __name__ == '__main__':
    unittest.main()
