import threading

from indexes.hnsw import HNSWIndex
from indexes.brute_force import BruteForceIndex

from metrics.metrics import get_distance_function


class DocumentDB:

    # =====================================
    # INIT
    # =====================================

    def __init__(self):

        self.documents = {}

        self.next_id = 1

        self.lock = threading.Lock()

        # =====================================
        # SEARCH INDEXES
        # =====================================

        self.hnsw = HNSWIndex()

        self.bruteforce = BruteForceIndex()

        self.embedding_dims = 0

    # =====================================
    # INSERT
    # =====================================

    def insert(
        self,
        title,
        text,
        embedding
    ):

        if not embedding:

            raise ValueError(
                "Missing embedding"
            )

        with self.lock:

            # =================================
            # INITIALIZE DIMENSIONS
            # =================================

            if self.embedding_dims == 0:

                self.embedding_dims = len(
                    embedding
                )

            # =================================
            # VALIDATE DIMENSIONS
            # =================================

            elif (

                len(embedding)

                !=

                self.embedding_dims
            ):

                raise ValueError(

                    f"Embedding dimension mismatch. "

                    f"Expected {self.embedding_dims}, "

                    f"got {len(embedding)}"
                )

            # =================================
            # BUILD DOCUMENT
            # =================================

            document = {

                "id": self.next_id,

                "title": title,

                "text": text,

                "embedding": embedding,

                "metadata": title,

                "category": "document"
            }

            self.documents[
                self.next_id
            ] = document

            # =================================
            # INSERT INTO INDEXES
            # =================================

            self.hnsw.insert(
                document
            )

            self.bruteforce.insert(
                document
            )

            inserted_id = self.next_id

            self.next_id += 1

            return inserted_id

    # =====================================
    # REMOVE
    # =====================================

    def remove(self, doc_id):

        with self.lock:

            if doc_id not in self.documents:

                return False

            del self.documents[doc_id]

            self.hnsw.remove(doc_id)

            self.bruteforce.remove(doc_id)

            return True

    # =====================================
    # SEARCH
    # =====================================

    def search(
        self,
        query_embedding,
        k=3,
        metric="cosine",
        algorithm="auto",
        max_distance=None
    ):

        if not query_embedding:

            return []

        with self.lock:

            # =================================
            # EMPTY DATABASE
            # =================================

            if len(self.documents) == 0:

                return []

            # =================================
            # DIMENSION CHECK
            # =================================

            if (

                len(query_embedding)

                !=

                self.embedding_dims
            ):

                raise ValueError(

                    f"Query dimension mismatch. "

                    f"Expected {self.embedding_dims}, "

                    f"got {len(query_embedding)}"
                )

            # =================================
            # DISTANCE FUNCTION
            # =================================

            distance_function = (
                get_distance_function(metric)
            )

            # =================================
            # AUTO ALGORITHM
            # =================================

            if algorithm == "auto":

                if len(self.documents) < 10:

                    algorithm = "bruteforce"

                else:

                    algorithm = "hnsw"

            # =================================
            # BRUTE FORCE
            # =================================

            if algorithm == "bruteforce":

                raw_results = (

                    self.bruteforce.search(

                        query_vector=query_embedding,

                        items=list(
                            self.documents.values()
                        ),

                        k=k,

                        distance_function=
                            distance_function
                    )
                )

            # =================================
            # HNSW
            # =================================

            elif algorithm == "hnsw":

                raw_results = (

                    self.hnsw.search(

                        query_vector=query_embedding,

                        k=k,

                        distance_function=
                            distance_function
                    )
                )

            # =================================
            # FALLBACK
            # =================================

            else:

                raw_results = (

                    self.bruteforce.search(

                        query_vector=query_embedding,

                        items=list(
                            self.documents.values()
                        ),

                        k=k,

                        distance_function=
                            distance_function
                    )
                )

            # =================================
            # FORMAT RESULTS
            # =================================

            results = []

            for result in raw_results:

                doc_id = result["id"]

                if doc_id not in self.documents:

                    continue

                distance = round(
                    result["distance"],
                    6
                )

                # =============================
                # MAX DISTANCE FILTER
                # =============================

                if (

                    max_distance is not None

                    and

                    distance > max_distance
                ):

                    continue

                similarity = round(

                    max(
                        0.0,
                        1.0 - distance
                    ),

                    6
                )

                results.append({

                    "id": doc_id,

                    "score":
                        similarity,

                    "distance":
                        distance,

                    "document":
                        self.documents[doc_id]
                })

            return results

    # =====================================
    # GET DOCUMENT
    # =====================================

    def get_document(self, doc_id):

        with self.lock:

            return self.documents.get(doc_id)

    # =====================================
    # GET ALL
    # =====================================

    def get_all(self):

        with self.lock:

            return list(
                self.documents.values()
            )

    # =====================================
    # CLEAR
    # =====================================

    def clear(self):

        with self.lock:

            self.documents = {}

            self.next_id = 1

            self.embedding_dims = 0

            self.hnsw = HNSWIndex()

            self.bruteforce = (
                BruteForceIndex()
            )

    # =====================================
    # SIZE
    # =====================================

    def size(self):

        with self.lock:

            return len(self.documents)

    # =====================================
    # GET DIMS
    # =====================================

    def get_dims(self):

        return self.embedding_dims

    # =====================================
    # INFO
    # =====================================

    def info(self):

        return {

            "documents":
                len(self.documents),

            "embedding_dims":
                self.embedding_dims,

            "hnsw":
                self.hnsw.info()
        }