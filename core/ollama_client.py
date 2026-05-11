import json
import os
import requests

from dotenv import load_dotenv

# =====================================
# LOAD ENV
# =====================================

load_dotenv()


class OllamaClient:

    # =====================================
    # INIT
    # =====================================

    def __init__(self):

        self.base_url = os.getenv(
            "OLLAMA_BASE_URL",
            "http://localhost:11434"
        ).rstrip("/")

        self.model = os.getenv(
            "OLLAMA_CHAT_MODEL",
            "llama3.2:1b"
        )

        self.embedding_model = os.getenv(
            "OLLAMA_EMBED_MODEL",
            "nomic-embed-text:latest"
        )

    # =====================================
    # STATUS
    # =====================================

    def status(self):

        try:

            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )

            if response.status_code == 200:
                return "online"

            return "offline"

        except Exception:

            return "offline"

    # =====================================
    # GENERATE TEXT
    # =====================================

    def generate(
        self,
        prompt,
        temperature=0.7,
        max_tokens=256
    ):

        try:

            payload = {

                "model": self.model,

                "prompt": prompt,

                "stream": False,

                "options": {

                    "temperature": temperature,

                    "num_predict": max_tokens
                }
            }

            response = requests.post(

                f"{self.base_url}/api/generate",

                json=payload,

                timeout=120
            )

            # =====================================
            # DEBUG
            # =====================================

            print("\n===== OLLAMA REQUEST =====")
            print("URL:", f"{self.base_url}/api/generate")
            print("MODEL:", self.model)
            print("==========================\n")

            print("STATUS CODE:", response.status_code)

            print("\nRAW RESPONSE:")
            print(response.text[:1000])
            print("\n==========================\n")

            response.raise_for_status()

            data = response.json()

            result = data.get(
                "response",
                ""
            )

            if not result:

                return "No response from model."

            return result.strip()

        except requests.exceptions.ConnectionError:

            return (
                "Cannot connect to Ollama. "
                "Make sure Ollama is running."
            )

        except requests.exceptions.HTTPError as e:

            return (
                f"Ollama HTTP error: {str(e)}"
            )

        except requests.exceptions.Timeout:

            return (
                "Ollama request timed out."
            )

        except Exception as e:

            return (
                f"Generation error: {str(e)}"
            )

    # =====================================
    # STREAM GENERATE
    # =====================================

    def generate_stream(
        self,
        prompt,
        temperature=0.7,
        max_tokens=256
    ):

        try:

            payload = {

                "model": self.model,

                "prompt": prompt,

                "stream": True,

                "options": {

                    "temperature": temperature,

                    "num_predict": max_tokens
                }
            }

            response = requests.post(

                f"{self.base_url}/api/generate",

                json=payload,

                stream=True,

                timeout=120
            )

            response.raise_for_status()

            for line in response.iter_lines():

                if not line:
                    continue

                try:

                    chunk = json.loads(
                        line.decode("utf-8")
                    )

                    token = chunk.get(
                        "response",
                        ""
                    )

                    if token:

                        yield token

                except json.JSONDecodeError:

                    continue

        except Exception as e:

            yield f"[ERROR] {str(e)}"

    # =====================================
    # EMBEDDINGS
    # =====================================

    def embed(self, text):

        try:

            payload = {

                "model": self.embedding_model,

                "prompt": text
            }

            response = requests.post(

                f"{self.base_url}/api/embeddings",

                json=payload,

                timeout=60
            )

            print("\n===== EMBEDDING REQUEST =====")
            print("MODEL:", self.embedding_model)
            print("STATUS:", response.status_code)
            print("=============================\n")

            response.raise_for_status()

            data = response.json()

            embedding = data.get(
                "embedding"
            )

            if embedding is None:

                raise ValueError(
                    "No embedding returned."
                )

            return embedding

        except requests.exceptions.ConnectionError:

            raise RuntimeError(
                "Cannot connect to Ollama."
            )

        except requests.exceptions.HTTPError as e:

            raise RuntimeError(
                f"Ollama HTTP error: {str(e)}"
            )

        except Exception as e:

            raise RuntimeError(
                f"Embedding error: {str(e)}"
            )