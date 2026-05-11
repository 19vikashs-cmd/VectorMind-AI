
from core.ollama_client import OllamaClient

ollama = OllamaClient()

print("Ollama online:", ollama.status())

embedding = ollama.embed("hello world")

print("Embedding size:", len(embedding))

answer = ollama.generate("What is AI?")

print(answer)

