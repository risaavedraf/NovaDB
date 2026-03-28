"""
NovaDB MCP Server - Configuration

Handles environment variables and default settings.
Automatically loads .env from the monorepo root on startup.
"""

import os
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Auto-load .env from the monorepo root (2 levels up from this file)
# This works regardless of the cwd when the MCP server is spawned
_monorepo_root = Path(__file__).parent.parent.parent.parent.parent
_env_file = _monorepo_root / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        pass  # python-dotenv not installed — fall back to env vars only

logger = logging.getLogger(__name__)


@dataclass
class NovaDBConfig:
    """Configuration for NovaDB MCP Server."""
    
    # Paths
    db_path: str = field(default_factory=lambda: os.environ.get(
        "NOVADB_PATH", "nova_production.msgpack"
    ))
    
    # Embeddings
    gemini_api_key: Optional[str] = field(default_factory=lambda: os.environ.get(
        "GEMINI_API_KEY"
    ))
    
    # NovaDB settings
    k_vecinos: int = 5
    umbral_padre: float = 0.50
    umbral_vecino: float = 0.45
    access_boost: float = 0.15
    decay_rate: float = 0.0001
    relevancia_weight: float = 0.3
    
    # Logging
    log_level: str = field(default_factory=lambda: os.environ.get(
        "NOVADB_LOG_LEVEL", "INFO"
    ))
    
    def setup_logging(self) -> None:
        """Configure logging to FILE (not console) to avoid corrupting MCP stdio stream."""
        import tempfile
        import sys
        level = getattr(logging, self.log_level.upper(), logging.INFO)
        
        # Log to file - NEVER to stdout/stderr in MCP mode
        log_file = os.environ.get("NOVADB_LOG_FILE", 
            os.path.join(tempfile.gettempdir(), "novadb-mcp.log"))
        
        # Remove all existing handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # File handler only
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        ))
        
        logging.root.setLevel(level)
        logging.root.addHandler(file_handler)
        
        # Suppress ALL console output from other loggers (novaDB engine, etc.)
        logging.getLogger().setLevel(logging.WARNING)
        for name in ['novadb', 'novadb_mcp', 'httpx', 'google']:
            logging.getLogger(name).setLevel(logging.WARNING)
        logging.getLogger('novadb_mcp').setLevel(level)
    
    @property
    def is_gemini_available(self) -> bool:
        """Check if Gemini API is configured."""
        return bool(self.gemini_api_key)

def get_config() -> NovaDBConfig:
    """Get configuration from environment."""
    return NovaDBConfig()
