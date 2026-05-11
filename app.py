from flask import (
    Flask,
    jsonify,
    request,
    render_template
)

from sklearn.decomposition import PCA

from core.vector_db import VectorDB
from core.document_db import DocumentDB
from core.ollama_client import OllamaClient

from embedding import embed_text

import numpy as np
import time
import random

# =========================================
# APP
# =========================================

app = Flask(__name__)

# =========================================
# INIT
# =========================================

EMBEDDING_DIMS = 384

vector_db = VectorDB(
    dims=EMBEDDING_DIMS
)

document_db = DocumentDB()

ollama = OllamaClient()

# =========================================
# DEMO DATA
# =========================================

print("\nLoading semantic demo vectors...\n")

demo_texts = [

    ("Binary trees and recursion", "cs"),
    ("Neural networks and AI", "cs"),
    ("Deep learning transformers", "cs"),
    ("Python backend engineering", "cs"),
    ("Machine learning embeddings", "cs"),

    ("Pizza with extra cheese", "food"),
    ("Burger and french fries", "food"),
    ("Italian pasta recipe", "food"),
    ("Chocolate ice cream dessert", "food"),
    ("Spicy chicken biryani", "food"),

    ("Basketball championship", "sports"),
    ("Football world cup", "sports"),
    ("Tennis grand slam", "sports"),
    ("Olympic running race", "sports"),
    ("Cricket batting practice", "sports"),

    ("Linear algebra vectors", "math"),
    ("Calculus integration theorem", "math"),
    ("Matrix multiplication", "math"),
    ("Probability and statistics", "math"),
    ("Geometry triangle formula", "math")
]

# =========================================
# LOAD DEMO DATA
# =========================================

for i in range(300):

    try:

        text, category = random.choice(
            demo_texts
        )

        metadata = f"{text} #{i}"

        embedding = embed_text(
            metadata
        )

        if embedding:

            vector_db.insert(

                vector=embedding,

                metadata=metadata,

                category=category
            )

    except Exception as e:

        print(
            f"Failed loading vector {i}: {e}"
        )

print(
    f"Loaded {vector_db.size()} semantic vectors.\n"
)

# =========================================
# HOME
# =========================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )

# =========================================
# STATUS
# =========================================

@app.route("/status")
def status():

    return jsonify({

        "status": "running",

        "ollama": ollama.status(),

        "vector_count": vector_db.size(),

        "document_count": document_db.size()
    })

# =========================================
# GET ITEMS
# =========================================

@app.route("/items")
def items():

    try:

        all_items = vector_db.get_all_items()

        cleaned = []

        for item in all_items:

            cleaned.append({

                "id":
                    item.get("id"),

                "metadata":
                    item.get("metadata"),

                "category":
                    item.get("category")
            })

        return jsonify(cleaned)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

# =========================================
# INSERT VECTOR
# =========================================

@app.route(
    "/insert-vector",
    methods=["POST"]
)
def insert_vector():

    try:

        data = request.json or {}

        metadata = data.get(
            "metadata",
            ""
        ).strip()

        category = data.get(
            "category",
            "general"
        ).strip()

        if not metadata:

            return jsonify({

                "success": False,

                "error": "Missing metadata"

            }), 400

        embedding = embed_text(
            metadata
        )

        inserted_id = vector_db.insert(

            vector=embedding,

            metadata=metadata,

            category=category
        )

        return jsonify({

            "success": True,

            "id": inserted_id,

            "metadata": metadata,

            "category": category,

            "vector_count":
                vector_db.size(),

            "message":
                f"Inserted '{metadata}'"
        })

    except Exception as e:

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500

# =========================================
# SEARCH
# =========================================

@app.route("/search")
def search():

    try:

        query = request.args.get(
            "q",
            ""
        ).strip()

        algorithm = request.args.get(
            "algo",
            "hnsw"
        )

        metric = request.args.get(
            "metric",
            "cosine"
        )

        k = int(
            request.args.get("k", 5)
        )

        if not query:

            return jsonify({
                "error": "Missing query"
            }), 400

        query_vector = embed_text(
            query
        )

        start = time.time()

        results = vector_db.search(

            query_vector=query_vector,

            k=max(1, min(k, 20)),

            metric=metric,

            algorithm=algorithm
        )

        latency_us = int(

            (time.time() - start)

            * 1_000_000
        )

        formatted = []

        for item in results:

            formatted.append({

                "id":
                    item.get("id"),

                "metadata":
                    item.get("metadata"),

                "category":
                    item.get("category"),

                "distance":
                    round(
                        item.get("distance", 0),
                        4
                    ),

                "score":
                    round(
                        item.get("score", 0),
                        4
                    )
            })

        return jsonify({

            "query": query,

            "algorithm":
                algorithm,

            "metric":
                metric,

            "latencyUs":
                latency_us,

            "count":
                len(formatted),

            "results":
                formatted
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

# =========================================
# BENCHMARK
# =========================================

@app.route("/benchmark")
def benchmark():

    try:

        query_vector = embed_text(
            "semantic vector search"
        )

        benchmark_data = vector_db.benchmark(

            query_vector=query_vector,

            k=5,

            metric="cosine"
        )

        return jsonify({

            "bruteforce": {

                "time_ms":

                    round(

                        benchmark_data[
                            "bruteforceUs"
                        ] / 1000,

                        4
                    )
            },

            "kdtree": {

                "time_ms":

                    round(

                        benchmark_data[
                            "kdtreeUs"
                        ] / 1000,

                        4
                    )
            },

            "hnsw": {

                "time_ms":

                    round(

                        benchmark_data[
                            "hnswUs"
                        ] / 1000,

                        4
                    )
            }
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

# =========================================
# CHAT
# =========================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    try:

        data = request.json or {}

        message = data.get(
            "message",
            ""
        ).strip()

        if not message:

            return jsonify({
                "error": "Empty message"
            }), 400

        print("\n===== USER MESSAGE =====")
        print(message)

        context = ""

        try:

            query_embedding = embed_text(
                message
            )

            results = document_db.search(

                query_embedding=query_embedding,

                k=5
            )

            for item in results:

                doc = item.get(
                    "document",
                    {}
                )

                text = doc.get(
                    "text",
                    ""
                )

                if text:

                    context += text + "\n\n"

        except Exception as e:

            print(
                "Document search failed:",
                e
            )

        if context.strip():

            prompt = f"""
You are VectorMind AI.

Use the context to answer.

CONTEXT:
{context}

QUESTION:
{message}

ANSWER:
"""

        else:

            prompt = f"""
You are VectorMind AI.

Answer naturally.

QUESTION:
{message}

ANSWER:
"""

        print("\n===== PROMPT =====")
        print(prompt)

        response = ollama.generate(

            prompt=prompt,

            temperature=0.7,

            max_tokens=256
        )

        print("\n===== MODEL RESPONSE =====")
        print(response)

        if not response:

            response = "No response generated."

        return jsonify({
            "response": response,
            "matches": results
        })

    except Exception as e:

        print(
            "CHAT ERROR:",
            str(e)
        )

        return jsonify({

            "error": str(e)
        }), 500

# =========================================
# INSERT DOCUMENT
# =========================================

@app.route(
    "/doc/insert",
    methods=["POST"]
)
def insert_document():

    try:

        data = request.json or {}

        title = data.get(
            "title",
            ""
        ).strip()

        text = data.get(
            "text",
            ""
        ).strip()

        if not title or not text:

            return jsonify({

                "success": False,

                "error":
                    "Missing title or text"

            }), 400

        chunks = [

            text[i:i + 500]

            for i in range(
                0,
                len(text),
                500
            )
        ]

        inserted = 0

        for chunk in chunks:

            embedding = embed_text(
                chunk
            )

            document_db.insert(

                title,

                chunk,

                embedding
            )

            inserted += 1

        return jsonify({

            "success": True,

            "chunks": inserted,

            "message":
                f"Inserted {inserted} chunks"
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

# =========================================
# PCA
# =========================================

@app.route("/pca")
def pca():

    try:

        items = vector_db.get_all_items()

        if not items:

            return jsonify([])

        vectors = []
        valid_items = []

        for item in items:

            embedding = item.get(
                "embedding"
            )

            if embedding:

                vectors.append(
                    embedding
                )

                valid_items.append(
                    item
                )

        if len(vectors) < 2:

            return jsonify([])

        vectors = np.array(
            vectors
        )

        pca_model = PCA(
            n_components=2
        )

        reduced = pca_model.fit_transform(
            vectors
        )

        output = []

        for i, item in enumerate(valid_items):

            output.append({

                "id":
                    item.get("id"),

                "x":
                    float(reduced[i][0]),

                "y":
                    float(reduced[i][1]),

                "category":
                    item.get(
                        "category",
                        "general"
                    ),

                "metadata":
                    item.get(
                        "metadata",
                        ""
                    )
            })

        return jsonify(output)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

# =========================================
# RUN
# =========================================

if __name__ == "__main__":

    app.run(

        debug=True,

        host="0.0.0.0",

        port=8080
    )

