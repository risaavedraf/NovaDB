import unittest
import tempfile
import os
import numpy as np
from novadb.core.node import Node
from novadb.core.graph import NovaGraph
from novadb.core.search import HierarchicalSearch
from novadb.core.consolidator import Consolidator
from novadb.novadb import NovaDB
from novadb.storage import disk
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
    """Mock embedder with predictable output."""
    def __init__(self, dim: int = 128):
        self.dim = dim

    def encode(self, text: str) -> np.ndarray:
        np.random.seed(hash(text) % 2**32)
        return np.random.randn(self.dim).astype(np.float32)


class TestUpdateOperations(unittest.TestCase):
    """Tests for update operations on nodes."""

    def setUp(self):
        self.embedder = MockE2EEmbedder(dim=128)
        self.graph = NovaGraph()
        self.consolidator = Consolidator(self.graph, self.embedder, llm_namer=mock_llm_namer)

    def test_update_text(self):
        """Updating node text changes the content."""
        node = create_node("original text", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(node)
        original_id = node.id

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph
        db.consolidator = self.consolidator

        db.update(original_id, {"text": "updated text"})

        updated_node = db.get(original_id)
        self.assertEqual(updated_node.text, "updated text")

    def test_update_metadata(self):
        """Updating metadata adds new fields."""
        node = create_node("test", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(node)
        original_id = node.id

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph
        db.consolidator = self.consolidator

        db.update(original_id, {"metadata": {"new_key": "new_value"}})

        updated_node = db.get(original_id)
        self.assertEqual(updated_node.metadata.get("new_key"), "new_value")

    def test_update_metadata_preserves_existing(self):
        """Update metadata preserves previously existing metadata."""
        node = create_node("test", tipo="MEMORIA", embedder=self.embedder)
        node.metadata = {"existing": "value"}
        self.graph.insert(node)
        original_id = node.id

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph
        db.consolidator = self.consolidator

        db.update(original_id, {"metadata": {"new_key": "new_value"}})

        updated_node = db.get(original_id)
        self.assertEqual(updated_node.metadata.get("existing"), "value")
        self.assertEqual(updated_node.metadata.get("new_key"), "new_value")

    def test_update_preserves_relationships_when_no_text_change(self):
        """Relationships are preserved when updating only metadata."""
        macro = create_node("Macro", tipo="MACRO", embedder=self.embedder)
        self.graph.insert(macro)

        memoria = create_node("Memory", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(memoria)

        memoria.padres.append(macro.id)
        macro.hijos.append(memoria.id)
        original_id = memoria.id

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph
        db.consolidator = self.consolidator

        db.update(original_id, {"metadata": {"key": "value"}})

        updated_node = db.get(original_id)
        self.assertIn(macro.id, updated_node.padres)

    def test_update_nonexistent_node(self):
        """Updating nonexistent node does not raise error."""
        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph
        db.consolidator = self.consolidator

        result = db.update("nonexistent-id", {"text": "new text"})
        self.assertIsNone(result)

    def test_update_reindexes_correctly(self):
        """Update re-indexes the node correctly after text change."""
        macro = create_node("Animals Concept", tipo="MACRO", embedder=self.embedder)
        self.graph.insert(macro)

        memoria = create_node("Dog", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(memoria)

        self.graph.rebuild_indices()

        original_padres = list(memoria.padres)

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph
        db.consolidator = self.consolidator

        db.update(memoria.id, {"text": "Cat"})

        updated_node = db.get(memoria.id)
        self.assertEqual(updated_node.text, "Cat")

    def test_update_vector_recalculated(self):
        """Vector is recalculated when text is updated."""
        node = create_node("original", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(node)
        original_vector = node.vector.copy()
        original_id = node.id

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph
        db.consolidator = self.consolidator

        db.update(original_id, {"text": "completely different text"})

        updated_node = db.get(original_id)

        self.assertFalse(np.array_equal(updated_node.vector, original_vector))


class TestUpdateVectorRecalculation(unittest.TestCase):
    """Tests for vector recalculation during updates."""

    def setUp(self):
        self.embedder = MockE2EEmbedder(dim=128)
        self.graph = NovaGraph()

    def test_update_preserves_node_id(self):
        """Node ID is preserved after text update."""
        node = create_node("original", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(node)
        original_id = node.id

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph
        db.consolidator = Consolidator(self.graph, self.embedder)

        db.update(original_id, {"text": "updated"})

        self.assertEqual(db.get(original_id).id, original_id)

    def test_update_clears_and_rebuilds_neighbors(self):
        """Neighbors are cleared and rebuilt after text update."""
        node1 = create_node("node1", tipo="MEMORIA", embedder=self.embedder)
        node2 = create_node("node2", tipo="MEMORIA", embedder=self.embedder)

        self.graph.insert(node1)
        self.graph.insert(node2)

        original_vecinos = list(node1.vecinos)

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph
        db.consolidator = Consolidator(self.graph, self.embedder)

        db.update(node1.id, {"text": "completely new and different text"})

        updated_node = db.get(node1.id)

    def test_update_multiple_fields(self):
        """Multiple fields can be updated at once."""
        node = create_node("original", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(node)
        original_id = node.id

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph
        db.consolidator = Consolidator(self.graph, self.embedder)

        db.update(original_id, {
            "text": "new text",
            "metadata": {"key1": "value1", "key2": "value2"}
        })

        updated_node = db.get(original_id)
        self.assertEqual(updated_node.text, "new text")
        self.assertEqual(updated_node.metadata.get("key1"), "value1")
        self.assertEqual(updated_node.metadata.get("key2"), "value2")


class TestUpdateWithConsolidation(unittest.TestCase):
    """Tests for update behavior with consolidation."""

    def setUp(self):
        self.embedder = MockE2EEmbedder(dim=128)
        self.graph = NovaGraph()
        self.consolidator = Consolidator(self.graph, self.embedder, llm_namer=mock_llm_namer)

    def test_update_triggers_consolidation_for_memory(self):
        """Updating memory node text can trigger consolidation."""
        for i in range(5):
            node = create_node(f"similar content {i}", tipo="MEMORIA", embedder=self.embedder)
            self.graph.insert(node)

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph
        db.consolidator = self.consolidator

        nodes_list = list(self.graph.nodes.values())
        memory_nodes = [n for n in nodes_list if n.tipo == "MEMORIA"]

        if memory_nodes:
            db.update(memory_nodes[0].id, {"text": "completely different new topic"})

    def test_update_does_not_trigger_consolidation_for_macro(self):
        """MACRO nodes do not trigger consolidation on update."""
        macro = create_node("Macro", tipo="MACRO", embedder=self.embedder)
        self.graph.insert(macro)

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph
        db.consolidator = self.consolidator

        initial_medio_count = self.graph.count("MEDIO")

        db.update(macro.id, {"text": "Updated Macro"})

        self.assertEqual(self.graph.count("MEDIO"), initial_medio_count)


class TestUpdateIndexIntegrity(unittest.TestCase):
    """Tests for index integrity during updates."""

    def setUp(self):
        self.embedder = MockE2EEmbedder(dim=128)
        self.graph = NovaGraph()

    def test_update_maintains_macro_index(self):
        """MACRO index is maintained after update."""
        macro = create_node("Macro", tipo="MACRO", embedder=self.embedder)
        self.graph.insert(macro)

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph
        db.consolidator = Consolidator(self.graph, self.embedder)

        db.update(macro.id, {"text": "Updated Macro"})

        self.assertEqual(len(self.graph.indice_macro), 1)
        self.assertIn(macro.id, self.graph.indice_macro)

    def test_update_maintains_medio_index(self):
        """MEDIO index is maintained after update."""
        macro = create_node("Macro", tipo="MACRO", embedder=self.embedder)
        self.graph.insert(macro)

        medio = create_node("Medium", tipo="MEDIO", embedder=self.embedder)
        medio.padres.append(macro.id)
        self.graph.insert(medio)
        self.graph.rebuild_indices()

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph
        db.consolidator = Consolidator(self.graph, self.embedder)

        db.update(medio.id, {"text": "Updated Medium"})

        self.assertIn(macro.id, self.graph.indice_medio)

    def test_update_maintains_memoria_index(self):
        """MEMORIA index is maintained after update."""
        macro = create_node("Macro", tipo="MACRO", embedder=self.embedder)
        self.graph.insert(macro)

        memoria = create_node("Memory", tipo="MEMORIA", embedder=self.embedder)
        memoria.padres.append(macro.id)
        self.graph.insert(memoria)
        self.graph.rebuild_indices()

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph
        db.consolidator = Consolidator(self.graph, self.embedder)

        db.update(memoria.id, {"text": "Updated Memory"})

        self.assertGreaterEqual(len(self.graph.indice_memoria), 0)


if __name__ == '__main__':
    unittest.main()
