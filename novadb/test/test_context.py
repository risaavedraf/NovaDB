import unittest
import numpy as np
from novadb.core.node import Node
from novadb.core.graph import NovaGraph
from novadb.core.search import HierarchicalSearch
from novadb.novadb import NovaDB
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


class MockE2EEmbedder(BaseEmbedder):
    """Mock embedder with predictable output."""
    def __init__(self, dim: int = 128):
        self.dim = dim

    def encode(self, text: str) -> np.ndarray:
        np.random.seed(hash(text) % 2**32)
        return np.random.randn(self.dim).astype(np.float32)


class TestContextRetrieval(unittest.TestCase):
    """Tests for context retrieval functionality."""

    def setUp(self):
        self.embedder = MockE2EEmbedder(dim=128)
        self.graph = NovaGraph()

    def _create_hierarchical_structure(self) -> dict:
        """Creates a hierarchical structure and returns node IDs."""
        macro = create_node("Animals", tipo="MACRO", embedder=self.embedder)
        self.graph.insert(macro)

        medio1 = create_node("Mammals", tipo="MEDIO", embedder=self.embedder)
        medio1.padres.append(macro.id)
        self.graph.insert(medio1)

        medio2 = create_node("Birds", tipo="MEDIO", embedder=self.embedder)
        medio2.padres.append(macro.id)
        self.graph.insert(medio2)

        memoria1 = create_node("Dog", tipo="MEMORIA", embedder=self.embedder)
        memoria1.padres.append(medio1.id)
        self.graph.insert(memoria1)

        memoria2 = create_node("Cat", tipo="MEMORIA", embedder=self.embedder)
        memoria2.padres.append(medio1.id)
        self.graph.insert(memoria2)

        memoria3 = create_node("Eagle", tipo="MEMORIA", embedder=self.embedder)
        memoria3.padres.append(medio2.id)
        self.graph.insert(memoria3)

        macro.hijos.extend([medio1.id, medio2.id])
        medio1.hijos.extend([memoria1.id, memoria2.id])
        medio2.hijos.append(memoria3.id)

        memoria1.vecinos.append(memoria2.id)
        memoria2.vecinos.append(memoria1.id)

        self.graph.rebuild_indices()

        return {
            "macro": macro,
            "medio1": medio1,
            "medio2": medio2,
            "memoria1": memoria1,
            "memoria2": memoria2,
            "memoria3": memoria3
        }

    def test_get_context_depth_1(self):
        """Context retrieval with depth 1 returns direct neighbors."""
        nodes = self._create_hierarchical_structure()
        memoria1 = nodes["memoria1"]

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph

        context = db.get_context(memoria1.id, depth=1)

        self.assertIn("centro", context)
        self.assertEqual(context["centro"]["text"], "Dog")
        self.assertIn("vecinos", context)

    def test_get_context_depth_2(self):
        """Context retrieval with depth 2 returns extended context."""
        nodes = self._create_hierarchical_structure()
        memoria1 = nodes["memoria1"]

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph

        context = db.get_context(memoria1.id, depth=2)

        self.assertIn("centro", context)
        self.assertIn("padres", context)
        self.assertIn("hijos", context)
        self.assertIn("vecinos", context)

    def test_get_context_with_vecinos(self):
        """Context includes neighbors correctly."""
        nodes = self._create_hierarchical_structure()
        memoria1 = nodes["memoria1"]

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph

        context = db.get_context(memoria1.id, depth=1)

        vecino_ids = [v["id"] for v in context.get("vecinos", [])]
        self.assertIn(memoria1.vecinos[0], vecino_ids)

    def test_get_context_nonexistent_node(self):
        """Context for nonexistent node returns empty dict."""
        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph

        context = db.get_context("nonexistent-id", depth=2)
        self.assertEqual(context, {})

    def test_get_context_circular_references(self):
        """Context handles circular references without infinite loops."""
        node_a = create_node("A", tipo="MEMORIA", embedder=self.embedder)
        node_b = create_node("B", tipo="MEMORIA", embedder=self.embedder)

        self.graph.insert(node_a)
        self.graph.insert(node_b)

        node_a.padres.append(node_b.id)
        node_b.hijos.append(node_a.id)
        node_b.padres.append(node_a.id)
        node_a.hijos.append(node_b.id)

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph

        context = db.get_context(node_a.id, depth=2)
        self.assertIn("centro", context)

    def test_get_context_includes_padres(self):
        """Context includes parent nodes."""
        nodes = self._create_hierarchical_structure()
        memoria1 = nodes["memoria1"]

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph

        context = db.get_context(memoria1.id, depth=2)

        parent_ids = [p["id"] for p in context.get("padres", [])]
        self.assertIn(nodes["medio1"].id, parent_ids)

    def test_get_context_includes_hijos(self):
        """Context includes child nodes."""
        nodes = self._create_hierarchical_structure()
        medio1 = nodes["medio1"]

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph

        context = db.get_context(medio1.id, depth=2)

        child_ids = [h["id"] for h in context.get("hijos", [])]
        self.assertIn(nodes["memoria1"].id, child_ids)
        self.assertIn(nodes["memoria2"].id, child_ids)


class TestContextRetrievalEdgeCases(unittest.TestCase):
    """Edge case tests for context retrieval."""

    def setUp(self):
        self.embedder = MockE2EEmbedder(dim=128)
        self.graph = NovaGraph()

    def test_get_context_no_parents(self):
        """Context for orphan node handles missing parents."""
        orphan = create_node("orphan", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(orphan)

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph

        context = db.get_context(orphan.id)

        self.assertEqual(context["centro"]["text"], "orphan")
        self.assertEqual(len(context.get("padres", [])), 0)

    def test_get_context_no_children(self):
        """Context for leaf node handles missing children."""
        leaf = create_node("leaf", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(leaf)

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph

        context = db.get_context(leaf.id)

        self.assertEqual(context["centro"]["text"], "leaf")
        self.assertEqual(len(context.get("hijos", [])), 0)

    def test_get_context_no_vecinos(self):
        """Context for node without neighbors."""
        solo = create_node("solo", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(solo)

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph

        context = db.get_context(solo.id)

        self.assertEqual(context["centro"]["text"], "solo")
        self.assertEqual(len(context.get("vecinos", [])), 0)

    def test_get_context_vector_excluded(self):
        """Context response excludes vector data."""
        node = create_node("test", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(node)

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph

        context = db.get_context(node.id)

        self.assertNotIn("vector", context["centro"])


class TestContextRetrievalWithDeletedNodes(unittest.TestCase):
    """Tests for context retrieval when related nodes are deleted."""

    def setUp(self):
        self.embedder = MockE2EEmbedder(dim=128)
        self.graph = NovaGraph()

    def test_get_context_with_deleted_parent(self):
        """Context handles gracefully when parent is deleted."""
        macro = create_node("Macro", tipo="MACRO", embedder=self.embedder)
        self.graph.insert(macro)

        memoria = create_node("Memory", tipo="MEMORIA", embedder=self.embedder)
        memoria.padres.append(macro.id)
        self.graph.insert(memoria)

        del self.graph.nodes[macro.id]
        self.graph.rebuild_indices()

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph

        context = db.get_context(memoria.id)
        self.assertEqual(context["centro"]["text"], "Memory")

    def test_get_context_with_deleted_vecino(self):
        """Context handles gracefully when neighbor is deleted."""
        node1 = create_node("Node1", tipo="MEMORIA", embedder=self.embedder)
        node2 = create_node("Node2", tipo="MEMORIA", embedder=self.embedder)

        self.graph.insert(node1)
        self.graph.insert(node2)

        node1.vecinos.append(node2.id)
        node2.vecinos.append(node1.id)

        del self.graph.nodes[node2.id]

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph

        context = db.get_context(node1.id)
        self.assertEqual(context["centro"]["text"], "Node1")


class TestGetChildren(unittest.TestCase):
    """Tests for get_children method."""

    def setUp(self):
        self.embedder = MockE2EEmbedder(dim=128)
        self.graph = NovaGraph()

    def test_get_children_returns_direct_children(self):
        """get_children returns only direct children."""
        macro = create_node("Macro", tipo="MACRO", embedder=self.embedder)
        self.graph.insert(macro)

        child1 = create_node("Child1", tipo="MEMORIA", embedder=self.embedder)
        child1.padres.append(macro.id)
        self.graph.insert(child1)

        child2 = create_node("Child2", tipo="MEMORIA", embedder=self.embedder)
        child2.padres.append(macro.id)
        self.graph.insert(child2)

        macro.hijos.extend([child1.id, child2.id])

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph

        children = db.get_children(macro.id)

        self.assertEqual(len(children), 2)
        child_texts = [c["text"] for c in children]
        self.assertIn("Child1", child_texts)
        self.assertIn("Child2", child_texts)

    def test_get_children_nonexistent_node(self):
        """get_children for nonexistent node returns empty list."""
        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph

        children = db.get_children("nonexistent-id")
        self.assertEqual(children, [])

    def test_get_children_no_children(self):
        """get_children for node without children returns empty list."""
        orphan = create_node("orphan", tipo="MEMORIA", embedder=self.embedder)
        self.graph.insert(orphan)

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph

        children = db.get_children(orphan.id)
        self.assertEqual(children, [])

    def test_get_children_excludes_vector(self):
        """get_children response excludes vector data."""
        macro = create_node("Macro", tipo="MACRO", embedder=self.embedder)
        self.graph.insert(macro)

        child = create_node("Child", tipo="MEMORIA", embedder=self.embedder)
        child.padres.append(macro.id)
        self.graph.insert(child)
        macro.hijos.append(child.id)

        db = NovaDB(embedder=self.embedder, path=":memory:", autosave=False)
        db.graph = self.graph

        children = db.get_children(macro.id)
        self.assertNotIn("vector", children[0])


if __name__ == '__main__':
    unittest.main()
