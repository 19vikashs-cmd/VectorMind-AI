from metrics.metrics import get_distance_function


class BruteForceIndex:

    def __init__(self):

        self.items = []

    # =====================================
    # INSERT
    # =====================================

    def insert(self, item):

        self.items.append(item)

    # =====================================
    # REMOVE
    # =====================================

    def remove(self, item_id):

        self.items = [

            item

            for item in self.items

            if item["id"] != item_id
        ]

    # =====================================
    # CLEAR
    # =====================================

    def clear(self):

        self.items = []

    # =====================================
    # REBUILD
    # =====================================

    def rebuild(self, items):

        self.clear()

        for item in items:

            self.insert(item)

    # =====================================
    # SEARCH
    # =====================================

    def search(
        self,
        query_vector,
        items=None,
        k=3,
        metric="cosine",
        distance_function=None
    ):

        if items is None:

            items = self.items

        if distance_function is None:

            distance_function = get_distance_function(
                metric
            )

        results = []

        for item in items:

            distance = distance_function(

                query_vector,

                item["embedding"]
            )

            results.append({

                "id": item["id"],

                "metadata": item.get(
                    "metadata",
                    item.get("title", "")
                ),

                "category": item.get(
                    "category",
                    "document"
                ),

                "distance": round(
                    float(distance),
                    6
                ),

                "embedding": item["embedding"],

                "text": item.get(
                    "text",
                    ""
                )
            })

        results.sort(
            key=lambda x: x["distance"]
        )

        return results[:k]