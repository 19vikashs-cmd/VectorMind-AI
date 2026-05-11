# metrics/metrics.py

import math


# =====================================
# COSINE DISTANCE
# =====================================

def cosine_distance(a, b):

    dot_product = 0.0

    norm_a = 0.0

    norm_b = 0.0

    for x, y in zip(a, b):

        dot_product += x * y

        norm_a += x * x

        norm_b += y * y

    if norm_a == 0 or norm_b == 0:

        return 1.0

    similarity = dot_product / (

        math.sqrt(norm_a) *
        math.sqrt(norm_b)
    )

    return 1.0 - similarity


# =====================================
# EUCLIDEAN DISTANCE
# =====================================

def euclidean_distance(a, b):

    total = 0.0

    for x, y in zip(a, b):

        diff = x - y

        total += diff * diff

    return math.sqrt(total)


# =====================================
# MANHATTAN DISTANCE
# =====================================

def manhattan_distance(a, b):

    total = 0.0

    for x, y in zip(a, b):

        total += abs(x - y)

    return total


# =====================================
# DISTANCE FUNCTION SELECTOR
# =====================================

def get_distance_function(metric="cosine"):

    metric = metric.lower()

    if metric == "euclidean":

        return euclidean_distance

    elif metric == "manhattan":

        return manhattan_distance

    return cosine_distance