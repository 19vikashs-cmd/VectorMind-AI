from dataclasses import dataclass

@dataclass
class DocumentItem:
    id: int
    title: str
    text: str
    embedding: list