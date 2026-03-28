"""
NovaDB MCP Tests - Tools

Unit tests for each MCP tool.
"""

import pytest
from unittest.mock import patch, MagicMock

class TestMemoriaTools:
    """Tests for memoria tools."""
    
    @patch('novadb_mcp.tools.memoria.get_db')
    @patch('novadb_mcp.tools.memoria.get_config')
    def test_memorizar_success(self, mock_get_config, mock_get_db, mock_novadb):
        """Test successful memory creation."""
        mock_get_db.return_value = mock_novadb
        mock_get_config.return_value.db_path = "/tmp/test.msgpack"
        mock_novadb.insert.return_value = "test-node-123"
        
        from novadb_mcp.tools.memoria import memorizar
        result = memorizar(texto="Test memory", tipo="MEMORIA")
        
        assert result["success"] is True
        assert result["node_id"] == "test-node-123"
        mock_novadb.insert.assert_called_once()
    
    @patch('novadb_mcp.tools.memoria.get_db')
    def test_memorizar_empty_text(self, mock_get_db, mock_novadb):
        """Test memorizar with empty text."""
        mock_get_db.return_value = mock_novadb
        mock_novadb.insert.side_effect = ValueError("Text cannot be empty")
        
        from novadb_mcp.tools.memoria import memorizar
        result = memorizar(texto="")
        
        assert result["success"] is False
        assert "error" in result
    
    @patch('novadb_mcp.tools.memoria.get_db')
    def test_recordar_success(self, mock_get_db, mock_novadb, mock_node):
        """Test successful memory recall."""
        mock_get_db.return_value = mock_novadb
        mock_novadb.search.return_value = [(mock_node, 0.85)]
        
        from novadb_mcp.tools.memoria import recordar
        result = recordar(consulta="test query", cantidad=3)
        
        assert result["success"] is True
        assert "results" in result
        assert len(result["results"]) > 0
    
    @patch('novadb_mcp.tools.memoria.get_db')
    def test_obtener_success(self, mock_get_db, mock_novadb, mock_node):
        """Test successful node retrieval."""
        mock_get_db.return_value = mock_novadb
        mock_novadb.get.return_value = mock_node
        
        from novadb_mcp.tools.memoria import obtener
        result = obtener(node_id="test-node-123")
        
        assert result["success"] is True
        assert result["node"]["id"] == "test-node-123"
    
    @patch('novadb_mcp.tools.memoria.get_db')
    def test_obtener_not_found(self, mock_get_db, mock_novadb):
        """Test obtener with non-existent node."""
        mock_get_db.return_value = mock_novadb
        mock_novadb.get.return_value = None
        
        from novadb_mcp.tools.memoria import obtener
        result = obtener(node_id="non-existent")
        
        assert result["success"] is False
        assert "no encontrado" in result["error"].lower()


class TestContextoTools:
    """Tests for contexto tools."""
    
    @patch('novadb_mcp.tools.contexto.get_db')
    def test_reflejar_success(self, mock_get_db, mock_novadb):
        """Test successful context reflection."""
        mock_get_db.return_value = mock_novadb
        
        from novadb_mcp.tools.contexto import reflejar
        result = reflejar(node_id="test-node-123", profundidad=1)
        
        assert result["success"] is True
        assert "context" in result
    
    @patch('novadb_mcp.tools.contexto.get_db')
    @patch('novadb_mcp.tools.contexto.get_config')
    def test_actualizar_success(self, mock_get_config, mock_get_db, mock_novadb):
        """Test successful node update."""
        mock_get_db.return_value = mock_novadb
        mock_get_config.return_value.db_path = "/tmp/test.msgpack"
        
        from novadb_mcp.tools.contexto import actualizar
        result = actualizar(node_id="test-node-123", texto="Updated text")
        
        assert result["success"] is True
        mock_novadb.update.assert_called_once()
    
    @patch('novadb_mcp.tools.contexto.get_db')
    def test_actualizar_no_fields(self, mock_get_db, mock_novadb):
        """Test actualizar with no fields specified."""
        mock_get_db.return_value = mock_novadb
        
        from novadb_mcp.tools.contexto import actualizar
        result = actualizar(node_id="test-node-123")
        
        assert result["success"] is False
        assert "no se especificaron" in result["error"].lower()


class TestSistemaTools:
    """Tests for sistema tools."""
    
    @patch('novadb_mcp.tools.sistema.get_db')
    def test_analizar_success(self, mock_get_db, mock_novadb):
        """Test successful stats retrieval."""
        mock_get_db.return_value = mock_novadb
        
        from novadb_mcp.tools.sistema import analizar
        result = analizar()
        
        assert result["success"] is True
        assert "stats" in result
        assert result["stats"]["total_nodos"] == 100
    
    @patch('novadb_mcp.tools.sistema.get_db')
    @patch('novadb_mcp.tools.sistema.get_config')
    def test_rebalancear_success(self, mock_get_config, mock_get_db, mock_novadb):
        """Test successful rebalancing."""
        mock_get_db.return_value = mock_novadb
        mock_get_config.return_value.db_path = "/tmp/test.msgpack"
        
        from novadb_mcp.tools.sistema import rebalancear
        result = rebalancear()
        
        assert result["success"] is True
        mock_novadb.rebalancear.assert_called_once()


class TestAdminTools:
    """Tests for admin tools."""
    
    @patch('novadb_mcp.tools.admin.get_db')
    @patch('novadb_mcp.tools.admin.get_config')
    def test_guardar_success(self, mock_get_config, mock_get_db, mock_novadb):
        """Test successful save."""
        mock_get_db.return_value = mock_novadb
        mock_get_config.return_value.db_path = "/tmp/test.msgpack"
        
        from novadb_mcp.tools.admin import guardar
        result = guardar()
        
        assert result["success"] is True
        mock_novadb.save.assert_called_once()
    
    @patch('novadb_mcp.tools.admin.get_db')
    @patch('novadb_mcp.tools.admin.get_config')
    def test_guardar_custom_path(self, mock_get_config, mock_get_db, mock_novadb):
        """Test save with custom path."""
        mock_get_db.return_value = mock_novadb
        mock_get_config.return_value.db_path = "/tmp/test.msgpack"
        
        from novadb_mcp.tools.admin import guardar
        result = guardar(ruta="/custom/path.msgpack")
        
        assert result["success"] is True
        mock_novadb.save.assert_called_with("/custom/path.msgpack")
    
    @patch('novadb_mcp.tools.admin.get_db')
    @patch('novadb_mcp.tools.admin.get_config')
    def test_cargar_success(self, mock_get_config, mock_get_db, mock_novadb):
        """Test successful load."""
        mock_get_db.return_value = mock_novadb
        mock_get_config.return_value.db_path = "/tmp/test.msgpack"
        
        from novadb_mcp.tools.admin import cargar
        result = cargar()
        
        assert result["success"] is True
        mock_novadb.load.assert_called_once()
    
    @patch('novadb_mcp.tools.admin.get_db')
    def test_exportar_success(self, mock_get_db, mock_novadb):
        """Test successful export."""
        mock_get_db.return_value = mock_novadb
        
        from novadb_mcp.tools.admin import exportar
        result = exportar(ruta="/tmp/export.md")
        
        assert result["success"] is True
        mock_novadb.export_md.assert_called_once()
