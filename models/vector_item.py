from dataclasses import dataclass

@dataclass
class VectorItem:
    id: int
    metadata: str
    category: str
    embedding: list