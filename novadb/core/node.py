import uuid
import numpy as np
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Any, Literal

@dataclass
class Node:
    """
    Minimal unit of knowledge in NovaDB.
    """
    text: str
    vector: np.ndarray
    tipo: Literal["MACRO", "MEDIO", "MEMORIA"]
    
    # Identity and flexible metadata
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Hierarchy and Spatial Semantics
    padres: List[str] = field(default_factory=list)
    hijos: List[str] = field(default_factory=list)
    vecinos: List[str] = field(default_factory=list)
    conexiones: List[Dict[str, Any]] = field(default_factory=list)
    
    # Chronology and Dynamic Attention (Decay)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    accesos: int = 0
    relevancia: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the node to a structured dictionary, ready for JSON/MsgPack."""
        return {
            "id": self.id,
            "text": self.text,
            "vector": self.vector.tolist() if isinstance(self.vector, np.ndarray) else self.vector,
            "tipo": self.tipo,
            "metadata": self.metadata,
            "padres": self.padres,
            "hijos": self.hijos,
            "vecinos": self.vecinos,
            "conexiones": self.conexiones,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "accesos": self.accesos,
            "relevancia": self.relevancia
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        """Reconstruct a node instantly from the storage dictionary."""
        return cls(
            text=data["text"],
            vector=np.array(data["vector"], dtype=np.float32),
            tipo=data["tipo"],
            id=data.get("id", str(uuid.uuid4())),
            metadata=data.get("metadata", {}),
            padres=data.get("padres", []),
            hijos=data.get("hijos", []),
            vecinos=data.get("vecinos", []),
            conexiones=data.get("conexiones", []),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
            accesos=data.get("accesos", 0),
            relevancia=data.get("relevancia", 0.5)
        )
