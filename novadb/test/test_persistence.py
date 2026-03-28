import os
import json
import shutil
import unittest
import tempfile
import numpy as np
from datetime import datetime
from novadb.core.node import Node
from novadb.core.graph import NovaGraph
from novadb.storage import disk
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


class TestPersistenceRoundtrip(unittest.TestCase):
    """Tests for save/load roundtrip integrity."""

    def setUp(self):
        self.embedder = MockEmbedder(dim=128)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_graph_with_all_node_types(self) -> NovaGraph:
        """Creates a graph with all node types and relationships."""
        graph = NovaGraph(k_vecinos=5)

        macro = Node(
            text="Main Concept",
            vector=self.embedder.encode("Main Concept"),
            tipo="MACRO",
            metadata={"source": "test", "priority": 1},
            relevancia=0.9,
            accesos=10
        )

        medio = Node(
            text="Sub Concept",
            vector=self.embedder.encode("Sub Concept"),
            tipo="MEDIO",
            metadata={"auto_consolidated": True},
            relevancia=0.7,
            accesos=5
        )

        memoria1 = Node(
            text="Memory One",
            vector=self.embedder.encode("Memory One"),
            tipo="MEMORIA",
            metadata={"tag": "important"},
            relevancia=0.6,
            accesos=3
        )

        memoria2 = Node(
            text="Memory Two",
            vector=self.embedder.encode("Memory Two"),
            tipo="MEMORIA",
            metadata={"tag": "normal"},
            relevancia=0.5,
            accesos=1
        )

        graph.insert(macro)
        graph.insert(medio)
        graph.insert(memoria1)
        graph.insert(memoria2)

        medio.padres.append(macro.id)
        macro.hijos.append(medio.id)

        memoria1.padres.append(medio.id)
        memoria1.vecinos.append(memoria2.id)
        medio.hijos.append(memoria1.id)

        memoria2.padres.append(medio.id)
        memoria2.vecinos.append(memoria1.id)
        medio.hijos.append(memoria2.id)

        memoria1.conexiones.append({
            "target": memoria2.id,
            "tipo": "related",
            "peso": 0.8
        })

        graph.rebuild_indices()
        return graph

    def test_json_roundtrip_preserves_all_fields(self):
        """All node fields are preserved through JSON save/load."""
        graph = self._create_graph_with_all_node_types()
        json_path = os.path.join(self.temp_dir, "test.json")

        disk.save_to_json(graph, json_path)
        loaded_graph = disk.load_from_json(json_path)

        self.assertEqual(graph.count(), loaded_graph.count())
        self.assertEqual(graph.count("MACRO"), loaded_graph.count("MACRO"))
        self.assertEqual(graph.count("MEDIO"), loaded_graph.count("MEDIO"))
        self.assertEqual(graph.count("MEMORIA"), loaded_graph.count("MEMORIA"))

    def test_msgpack_roundtrip_preserves_all_fields(self):
        """All node fields are preserved through MsgPack save/load."""
        graph = self._create_graph_with_all_node_types()
        msgpack_path = os.path.join(self.temp_dir, "test.msgpack")

        disk.save_to_msgpack(graph, msgpack_path)
        loaded_graph = disk.load_from_msgpack(msgpack_path)

        self.assertEqual(graph.count(), loaded_graph.count())
        self.assertEqual(graph.count("MACRO"), loaded_graph.count("MACRO"))
        self.assertEqual(graph.count("MEDIO"), loaded_graph.count("MEDIO"))
        self.assertEqual(graph.count("MEMORIA"), loaded_graph.count("MEMORIA"))

    def test_roundtrip_preserves_indices(self):
        """Indices are correctly rebuilt after load."""
        graph = self._create_graph_with_all_node_types()
        json_path = os.path.join(self.temp_dir, "test.json")

        disk.save_to_json(graph, json_path)
        loaded_graph = disk.load_from_json(json_path)

        self.assertEqual(len(loaded_graph.indice_macro), len(graph.indice_macro))
        self.assertEqual(len(loaded_graph.indice_medio), len(graph.indice_medio))
        self.assertEqual(len(loaded_graph.indice_memoria), len(graph.indice_memoria))

    def test_roundtrip_preserves_relevancia(self):
        """Relevancia values are preserved after roundtrip."""
        graph = self._create_graph_with_all_node_types()
        msgpack_path = os.path.join(self.temp_dir, "test.msgpack")

        original_relevancias = {n.id: n.relevancia for n in graph.nodes.values()}

        disk.save_to_msgpack(graph, msgpack_path)
        loaded_graph = disk.load_from_msgpack(msgpack_path)

        for node_id, original_rel in original_relevancias.items():
            loaded_node = loaded_graph.nodes.get(node_id)
            self.assertIsNotNone(loaded_node)
            self.assertAlmostEqual(loaded_node.relevancia, original_rel, places=5)

    def test_roundtrip_preserves_accesos(self):
        """Accesos count is preserved after roundtrip."""
        graph = self._create_graph_with_all_node_types()
        json_path = os.path.join(self.temp_dir, "test.json")

        original_accesos = {n.id: n.accesos for n in graph.nodes.values()}

        disk.save_to_json(graph, json_path)
        loaded_graph = disk.load_from_json(json_path)

        for node_id, original_acc in original_accesos.items():
            loaded_node = loaded_graph.nodes.get(node_id)
            self.assertIsNotNone(loaded_node)
            self.assertEqual(loaded_node.accesos, original_acc)

    def test_roundtrip_preserves_relationships(self):
        """Parent/child/vecino relationships are preserved."""
        graph = self._create_graph_with_all_node_types()
        json_path = os.path.join(self.temp_dir, "test.json")

        original_rels = {}
        for node_id, node in graph.nodes.items():
            original_rels[node_id] = {
                "padres": list(node.padres),
                "hijos": list(node.hijos),
                "vecinos": list(node.vecinos)
            }

        disk.save_to_json(graph, json_path)
        loaded_graph = disk.load_from_json(json_path)

        for node_id, original_rel in original_rels.items():
            loaded_node = loaded_graph.nodes.get(node_id)
            self.assertIsNotNone(loaded_node)
            self.assertEqual(list(loaded_node.padres), original_rel["padres"])
            self.assertEqual(list(loaded_node.hijos), original_rel["hijos"])
            self.assertEqual(list(loaded_node.vecinos), original_rel["vecinos"])

    def test_roundtrip_preserves_metadata(self):
        """Metadata is preserved through roundtrip."""
        graph = self._create_graph_with_all_node_types()
        json_path = os.path.join(self.temp_dir, "test.json")

        original_meta = {n.id: dict(n.metadata) for n in graph.nodes.values()}

        disk.save_to_json(graph, json_path)
        loaded_graph = disk.load_from_json(json_path)

        for node_id, original_m in original_meta.items():
            loaded_node = loaded_graph.nodes.get(node_id)
            self.assertIsNotNone(loaded_node)
            self.assertEqual(loaded_node.metadata, original_m)

    def test_roundtrip_preserves_conexiones(self):
        """Conexiones are preserved through roundtrip."""
        graph = self._create_graph_with_all_node_types()
        msgpack_path = os.path.join(self.temp_dir, "test.msgpack")

        disk.save_to_msgpack(graph, msgpack_path)
        loaded_graph = disk.load_from_msgpack(msgpack_path)

        for node_id, node in graph.nodes.items():
            loaded_node = loaded_graph.nodes.get(node_id)
            self.assertEqual(len(loaded_node.conexiones), len(node.conexiones))

    def test_roundtrip_preserves_timestamps(self):
        """Created_at and updated_at timestamps are preserved."""
        graph = self._create_graph_with_all_node_types()
        json_path = os.path.join(self.temp_dir, "test.json")

        original_times = {n.id: (n.created_at, n.updated_at) for n in graph.nodes.values()}

        disk.save_to_json(graph, json_path)
        loaded_graph = disk.load_from_json(json_path)

        for node_id, (orig_created, orig_updated) in original_times.items():
            loaded_node = loaded_graph.nodes.get(node_id)
            self.assertIsNotNone(loaded_node)
            self.assertEqual(loaded_node.created_at, orig_created)
            self.assertEqual(loaded_node.updated_at, orig_updated)

    def test_roundtrip_preserves_k_vecinos(self):
        """Graph k_vecinos setting is preserved."""
        graph = NovaGraph(k_vecinos=10)
        json_path = os.path.join(self.temp_dir, "test.json")

        disk.save_to_json(graph, json_path)
        loaded_graph = disk.load_from_json(json_path)

        self.assertEqual(loaded_graph.k_vecinos, 10)


class TestPersistenceCorruption(unittest.TestCase):
    """Tests for handling corrupted or invalid files."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_nonexistent_json(self):
        """Loading nonexistent JSON file raises FileNotFoundError."""
        nonexistent = os.path.join(self.temp_dir, "nonexistent.json")
        with self.assertRaises(FileNotFoundError):
            disk.load_from_json(nonexistent)

    def test_load_nonexistent_msgpack(self):
        """Loading nonexistent MsgPack file raises FileNotFoundError."""
        nonexistent = os.path.join(self.temp_dir, "nonexistent.msgpack")
        with self.assertRaises(FileNotFoundError):
            disk.load_from_msgpack(nonexistent)

    def test_load_empty_json_file(self):
        """Loading empty JSON file raises JSONDecodeError."""
        empty_file = os.path.join(self.temp_dir, "empty.json")
        with open(empty_file, "w") as f:
            f.write("")

        with self.assertRaises(json.JSONDecodeError):
            disk.load_from_json(empty_file)

    def test_load_invalid_json_syntax(self):
        """Loading invalid JSON syntax raises JSONDecodeError."""
        invalid_file = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_file, "w") as f:
            f.write("{ invalid json }")

        with self.assertRaises(json.JSONDecodeError):
            disk.load_from_json(invalid_file)

    def test_load_json_wrong_structure(self):
        """Loading JSON with wrong structure creates empty graph (graceful degradation)."""
        wrong_struct = os.path.join(self.temp_dir, "wrong.json")
        with open(wrong_struct, "w") as f:
            json.dump({"wrong_key": "value"}, f)

        loaded_graph = disk.load_from_json(wrong_struct)
        self.assertEqual(loaded_graph.count(), 0)

    def test_load_json_missing_required_fields(self):
        """Loading JSON missing required node fields raises KeyError."""
        incomplete = os.path.join(self.temp_dir, "incomplete.json")
        with open(incomplete, "w") as f:
            json.dump({
                "version": "1.0",
                "k_vecinos": 5,
                "nodes": {
                    "test": {
                        "text": "test"
                    }
                }
            }, f)

        with self.assertRaises(KeyError):
            disk.load_from_json(incomplete)

    def test_load_corrupted_msgpack(self):
        """Loading corrupted MsgPack data raises Exception."""
        corrupted = os.path.join(self.temp_dir, "corrupted.msgpack")
        with open(corrupted, "wb") as f:
            f.write(b"not valid msgpack data")

        with self.assertRaises(Exception):
            disk.load_from_msgpack(corrupted)

    def test_load_truncated_msgpack(self):
        """Loading truncated MsgPack data raises Exception."""
        truncated = os.path.join(self.temp_dir, "truncated.msgpack")
        with open(truncated, "wb") as f:
            f.write(b"\x93\x01\x02")

        with self.assertRaises(Exception):
            disk.load_from_msgpack(truncated)


class TestPersistenceVectorIntegrity(unittest.TestCase):
    """Tests for vector preservation during roundtrip."""

    def setUp(self):
        self.embedder = MockEmbedder(dim=128)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_vector_values_preserved_json(self):
        """Vector values are exactly preserved through JSON."""
        graph = NovaGraph()
        node = create_node("test vector", tipo="MEMORIA", embedder=self.embedder)
        graph.insert(node)

        original_vector = node.vector.copy()
        json_path = os.path.join(self.temp_dir, "vectors.json")

        disk.save_to_json(graph, json_path)
        loaded_graph = disk.load_from_json(json_path)

        loaded_node = loaded_graph.nodes[node.id]
        np.testing.assert_array_almost_equal(loaded_node.vector, original_vector)

    def test_vector_values_preserved_msgpack(self):
        """Vector values are exactly preserved through MsgPack."""
        graph = NovaGraph()
        node = create_node("test vector", tipo="MEMORIA", embedder=self.embedder)
        graph.insert(node)

        original_vector = node.vector.copy()
        msgpack_path = os.path.join(self.temp_dir, "vectors.msgpack")

        disk.save_to_msgpack(graph, msgpack_path)
        loaded_graph = disk.load_from_msgpack(msgpack_path)

        loaded_node = loaded_graph.nodes[node.id]
        np.testing.assert_array_almost_equal(loaded_node.vector, original_vector)

    def test_vector_dtype_preserved(self):
        """Vector dtype is preserved through roundtrip."""
        graph = NovaGraph()
        node = create_node("dtype test", tipo="MEMORIA", embedder=self.embedder)

        self.assertEqual(node.vector.dtype, np.float32)

        graph.insert(node)
        json_path = os.path.join(self.temp_dir, "dtype.json")

        disk.save_to_json(graph, json_path)
        loaded_graph = disk.load_from_json(json_path)

        loaded_node = loaded_graph.nodes[node.id]
        self.assertEqual(loaded_node.vector.dtype, np.float32)


class TestPersistenceMultipleCycles(unittest.TestCase):
    """Tests for multiple save/load cycles."""

    def setUp(self):
        self.embedder = MockEmbedder(dim=128)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_multiple_json_save_load_cycles(self):
        """Data integrity after multiple save/load cycles."""
        graph = NovaGraph()
        node_ids = []
        for i in range(5):
            node = create_node(f"cycle test {i}", tipo="MEMORIA", embedder=self.embedder)
            graph.insert(node)
            node_ids.append(node.id)

        json_path = os.path.join(self.temp_dir, "cycles.json")

        for cycle in range(3):
            disk.save_to_json(graph, json_path)
            graph = disk.load_from_json(json_path)

            self.assertEqual(graph.count(), 5)
            for node_id in node_ids:
                self.assertIsNotNone(graph.nodes.get(node_id))

    def test_multiple_msgpack_save_load_cycles(self):
        """Data integrity after multiple MsgPack save/load cycles."""
        graph = NovaGraph()
        for i in range(5):
            node = create_node(f"msgpack cycle {i}", tipo="MEMORIA", embedder=self.embedder)
            graph.insert(node)

        msgpack_path = os.path.join(self.temp_dir, "cycles.msgpack")

        for cycle in range(3):
            disk.save_to_msgpack(graph, msgpack_path)
            graph = disk.load_from_msgpack(msgpack_path)

            self.assertEqual(graph.count(), 5)


if __name__ == '__main__':
    unittest.main()
