# utils/pca_visualizer.py

import matplotlib.pyplot as plt
import numpy as np

from sklearn.decomposition import PCA


def visualize_vectors(items):

    if not items:
        return

    vectors = []
    labels = []

    for item in items:

        embedding = item.get("embedding")

        if not embedding:
            continue

        vectors.append(embedding)

        labels.append(
            item.get(
                "category",
                "unknown"
            )
        )

    if len(vectors) < 2:
        return

    vectors = np.array(vectors)

    # =====================================
    # PCA REDUCTION
    # =====================================

    pca = PCA(n_components=2)

    reduced = pca.fit_transform(vectors)

    # =====================================
    # PLOT
    # =====================================

    plt.figure(figsize=(10, 8))

    for i, point in enumerate(reduced):

        x = point[0]
        y = point[1]

        plt.scatter(x, y)

        plt.text(

            x,

            y,

            labels[i],

            fontsize=8
        )

    plt.title(
        "VectorDB PCA Visualization"
    )

    plt.xlabel("PCA 1")

    plt.ylabel("PCA 2")

    plt.tight_layout()

    plt.savefig(
        "static/pca_plot.png"
    )

    plt.close()