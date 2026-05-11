# utils/generator.py

import random


def generate_vectors(
    count=1000,
    dims=16,
    seed=42
):

    random.seed(seed)

    categories = [

        "cs",
        "math",
        "food",
        "sports"
    ]

    items = []

    for i in range(count):

        vector = [

            round(random.random(), 6)

            for _ in range(dims)
        ]

        items.append({

            "metadata": f"Vector {i}",

            "category": random.choice(categories),

            "embedding": vector
        })

    return items