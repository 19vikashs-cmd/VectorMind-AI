# core/vector_db.py

import threading
import time

from indexes.brute_force import BruteForceIndex
from indexes.kd_tree import KDTreeIndex
from indexes.hnsw import HNSWIndex

from metrics.metrics import get_distance_function


class VectorDB:

    # =====================================
    # INIT
    # =====================================

    def __init__(self, dims=384):

        self.dims = dims

        self.items = {}

        self.next_id = 1

        self.lock = threading.Lock()

        # =====================================
        # SEARCH INDEXES
        # =====================================

        self.bruteforce = BruteForceIndex()

        self.kdtree = KDTreeIndex(dims)

        self.hnsw = HNSWIndex()

    # =====================================
    # VALIDATE VECTOR
    # =====================================

    def _validate_vector(self, vector):

        if not isinstance(vector, (list, tuple)):

            raise ValueError(
                "Vector must be a list or tuple"
            )

        if len(vector) != self.dims:

            raise ValueError(

                f"Embedding dimension mismatch. "

                f"Expected {self.dims}, "

                f"got {len(vector)}"
            )

    # =====================================
    # INSERT
    # =====================================

    def insert(
        self,
        vector,
        metadata,
        category="general"
    ):

        self._validate_vector(vector)

        with self.lock:

            item = {

                "id": self.next_id,

                "metadata": metadata,

                "category": category,

                "embedding": vector
            }

            self.items[self.next_id] = item

            # =================================
            # INSERT INTO INDEXES
            # =================================

            self.bruteforce.insert(item)

            self.kdtree.insert(item)

            self.hnsw.insert(item)

            inserted_id = self.next_id

            self.next_id += 1

            return inserted_id

    # =====================================
    # REMOVE
    # =====================================

    def remove(self, item_id):

        with self.lock:

            if item_id not in self.items:

                return False

            del self.items[item_id]

            self.bruteforce.remove(item_id)

            self.hnsw.remove(item_id)

            # =================================
            # REBUILD KD TREE
            # =================================

            remaining_items = list(
                self.items.values()
            )

            self.kdtree.rebuild(
                remaining_items
            )

            return True

    # =====================================
    # SEARCH
    # =====================================

    def search(
        self,
        query_vector,
        k=5,
        metric="cosine",
        algorithm="hnsw"
    ):

        self._validate_vector(query_vector)

        with self.lock:

            # =================================
            # DISTANCE FUNCTION
            # =================================

            distance_function = (
                get_distance_function(metric)
            )

            # =================================
            # SEARCH
            # =================================

            if algorithm == "bruteforce":

                raw_results = (

                    self.bruteforce.search(

                        query_vector=query_vector,

                        items=list(
                            self.items.values()
                        ),

                        k=k,

                        distance_function=
                        distance_function
                    )
                )

            elif algorithm == "kdtree":

                raw_results = (

                    self.kdtree.search(

                        query_vector=query_vector,

                        k=k,

                        distance_function=
                        distance_function
                    )
                )

            elif algorithm == "hnsw":

                raw_results = (

                    self.hnsw.search(

                        query_vector=query_vector,

                        k=k,

                        distance_function=
                        distance_function
                    )
                )

            else:

                raise ValueError(
                    f"Unsupported algorithm: {algorithm}"
                )

            # =================================
            # FORMAT RESULTS
            # =================================

            formatted_results = []

            for result in raw_results:

                item_id = result.get("id")

                if item_id not in self.items:

                    continue

                item = self.items[item_id]

                distance = round(
                    result.get("distance", 0),
                    6
                )

                # =================================
                # SCORE NORMALIZATION
                # =================================

                if metric == "cosine":

                    similarity = max(
                        0.0,
                        min(
                            1.0,
                            round(1.0 - distance, 6)
                        )
                    )

                else:

                    similarity = round(
                        1 / (1 + distance),
                        6
                    )

                formatted_results.append({

                    "id":
                    item["id"],

                    "metadata":
                    item["metadata"],

                    "category":
                    item["category"],

                    "distance":
                    distance,

                    "score":
                    similarity
                })

            return formatted_results

    # =====================================
    # BENCHMARK
    # =====================================

    def benchmark(
        self,
        query_vector,
        k=5,
        metric="cosine"
    ):

        self._validate_vector(query_vector)

        with self.lock:

            distance_function = (
                get_distance_function(metric)
            )

            # =================================
            # BRUTE FORCE
            # =================================

            start = time.perf_counter()

            self.bruteforce.search(

                query_vector=query_vector,

                items=list(
                    self.items.values()
                ),

                k=k,

                distance_function=
                distance_function
            )

            brute_us = int(

                (
                    time.perf_counter()
                    - start
                )

                * 1_000_000
            )

            # =================================
            # KD TREE
            # =================================

            start = time.perf_counter()

            self.kdtree.search(

                query_vector=query_vector,

                k=k,

                distance_function=
                distance_function
            )

            kd_us = int(

                (
                    time.perf_counter()
                    - start
                )

                * 1_000_000
            )

            # =================================
            # HNSW
            # =================================

            start = time.perf_counter()

            self.hnsw.search(

                query_vector=query_vector,

                k=k,

                distance_function=
                distance_function
            )

            hnsw_us = int(

                (
                    time.perf_counter()
                    - start
                )

                * 1_000_000
            )

            return {

                "bruteforceUs":
                brute_us,

                "kdtreeUs":
                kd_us,

                "hnswUs":
                hnsw_us,

                "itemCount":
                len(self.items)
            }

    # =====================================
    # GET ITEM
    # =====================================

    def get_item(self, item_id):

        with self.lock:

            return self.items.get(item_id)

    # =====================================
    # GET ALL ITEMS
    # =====================================

    def get_all_items(self):

        with self.lock:

            return list(
                self.items.values()
            )

    # =====================================
    # SIZE
    # =====================================

    def size(self):

        with self.lock:

            return len(self.items)

    # =====================================
    # CLEAR
    # =====================================

    def clear(self):

        with self.lock:

            self.items = {}

            self.next_id = 1

            self.bruteforce = (
                BruteForceIndex()
            )

            self.kdtree = KDTreeIndex(
                self.dims
            )

            self.hnsw = HNSWIndex()

    # =====================================
    # HNSW INFO
    # =====================================

    def get_hnsw_info(self):

        return self.hnsw.get_graph_info()

    # =====================================
    # KD TREE INFO
    # =====================================

    def get_kdtree_info(self):

        return {

            "dims":
            self.kdtree.dims,

            "has_root":
            self.kdtree.root
            is not None
        }

    # =====================================
    # DATABASE INFO
    # =====================================

    def get_stats(self):

        with self.lock:

            categories = {}

            for item in self.items.values():

                category = item.get(
                    "category",
                    "general"
                )

                categories[category] = (

                    categories.get(category, 0)
                    + 1
                )

            return {

                "dimensions":
                self.dims,

                "total_items":
                len(self.items),

                "categories":
                categories
            }