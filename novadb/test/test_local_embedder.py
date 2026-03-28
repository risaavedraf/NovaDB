import unittest
from unittest.mock import patch, MagicMock
import numpy as np

class TestLocalEmbedder(unittest.TestCase):
    
    def test_local_embedder_initialization(self):
        with patch('novadb.core.embedder.LocalEmbedder.__init__', return_value=None):
            from novadb.core.embedder import LocalEmbedder
            embedder = LocalEmbedder.__new__(LocalEmbedder)
            embedder._dims = 384
            embedder.model = MagicMock()
            self.assertEqual(embedder.dims, 384)
    
    def test_local_embedder_encode_returns_correct_dimensions(self):
        with patch('novadb.core.embedder.LocalEmbedder.__init__', return_value=None):
            from novadb.core.embedder import LocalEmbedder
            embedder = LocalEmbedder.__new__(LocalEmbedder)
            embedder._dims = 384
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([0.1] * 384)
            embedder.model = mock_model
            
            result = embedder.encode("test text")
            self.assertEqual(len(result), 384)
            mock_model.encode.assert_called_once_with("test text", convert_to_numpy=True)
    
    def test_local_embedder_encode_batch(self):
        with patch('novadb.core.embedder.LocalEmbedder.__init__', return_value=None):
            from novadb.core.embedder import LocalEmbedder
            embedder = LocalEmbedder.__new__(LocalEmbedder)
            embedder._dims = 384
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1] * 384, [0.2] * 384])
            embedder.model = mock_model
            
            texts = ["text1", "text2"]
            results = embedder.encode_batch(texts)
            
            self.assertEqual(len(results), 2)
            self.assertEqual(len(results[0]), 384)
            self.assertEqual(len(results[1]), 384)
            mock_model.encode.assert_called_once_with(texts, convert_to_numpy=True)
    
    def test_local_embedder_import_error(self):
        with patch.dict('sys.modules', {'sentence_transformers': None}):
            with self.assertRaises(ImportError) as context:
                from novadb.core.embedder import LocalEmbedder
                LocalEmbedder()
            self.assertIn("sentence-transformers", str(context.exception))

    def test_embedder_dims_property(self):
        from novadb.core.embedder import BaseEmbedder
        base = BaseEmbedder()
        self.assertIsNone(base.dims)

class TestEmbedderFallback(unittest.TestCase):
    
    @patch('novadb.novadb.GeminiEmbedder')
    @patch('novadb.novadb.LocalEmbedder')
    def test_novadb_falls_back_to_local_when_gemini_fails(self, mock_local, mock_gemini):
        mock_gemini.side_effect = ValueError("No API key")
        mock_local.return_value = MagicMock()
        
        from novadb.novadb import NovaDB
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.msgpack")
            with patch('novadb.novadb.os.path.exists', return_value=False):
                with patch('novadb.novadb.NovaGraph'):
                    db = NovaDB(embedder=None, path=db_path)
        
        mock_local.assert_called_once()
    
    @patch('novadb.novadb.GeminiEmbedder')
    def test_novadb_uses_gemini_when_available(self, mock_gemini):
        mock_gemini.return_value = MagicMock()
        
        from novadb.novadb import NovaDB
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.msgpack")
            with patch('novadb.novadb.os.path.exists', return_value=False):
                with patch('novadb.novadb.NovaGraph'):
                    db = NovaDB(embedder=None, path=db_path)
        
        mock_gemini.assert_called_once()

    def test_novadb_uses_custom_embedder(self):
        custom_embedder = MagicMock()
        
        from novadb.novadb import NovaDB
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.msgpack")
            with patch('novadb.novadb.os.path.exists', return_value=False):
                with patch('novadb.novadb.NovaGraph'):
                    db = NovaDB(embedder=custom_embedder, path=db_path)
        
        self.assertEqual(db.embedder, custom_embedder)


if __name__ == '__main__':
    unittest.main()
