import heapq

from metrics.metrics import get_distance_function


class KDTreeNode:

    def __init__(self, item):

        self.item = item

        self.left = None

        self.right = None


class KDTreeIndex:

    def __init__(self, dims=16):

        self.root = None

        self.dims = dims

    # =====================================
    # INSERT
    # =====================================

    def insert(self, item):

        self.root = self._insert(

            self.root,

            item,

            depth=0
        )

    def _insert(
        self,
        node,
        item,
        depth
    ):

        if node is None:

            return KDTreeNode(item)

        axis = depth % self.dims

        if (

            item["embedding"][axis]

            <

            node.item["embedding"][axis]
        ):

            node.left = self._insert(

                node.left,

                item,

                depth + 1
            )

        else:

            node.right = self._insert(

                node.right,

                item,

                depth + 1
            )

        return node

    # =====================================
    # SEARCH
    # =====================================

    def search(
        self,
        query_vector,
        k=3,
        metric="cosine",
        distance_function=None
    ):

        if distance_function is None:

            distance_function = get_distance_function(
                metric
            )

        heap = []

        self._search(

            node=self.root,

            query_vector=query_vector,

            k=k,

            depth=0,

            distance_function=distance_function,

            heap=heap
        )

        results = []

        while heap:

            negative_distance, item = heapq.heappop(
                heap
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
                    abs(negative_distance),
                    6
                ),

                "embedding": item["embedding"],

                "text": item.get(
                    "text",
                    ""
                )
            })

        results.reverse()

        return results

    # =====================================
    # INTERNAL SEARCH
    # =====================================

    def _search(
        self,
        node,
        query_vector,
        k,
        depth,
        distance_function,
        heap
    ):

        if node is None:

            return

        distance = distance_function(

            query_vector,

            node.item["embedding"]
        )

        if len(heap) < k:

            heapq.heappush(

                heap,

                (-distance, node.item)
            )

        else:

            if distance < abs(heap[0][0]):

                heapq.heappop(heap)

                heapq.heappush(

                    heap,

                    (-distance, node.item)
                )

        axis = depth % self.dims

        diff = (

            query_vector[axis]

            -

            node.item["embedding"][axis]
        )

        if diff < 0:

            near_branch = node.left

            far_branch = node.right

        else:

            near_branch = node.right

            far_branch = node.left

        self._search(

            near_branch,

            query_vector,

            k,

            depth + 1,

            distance_function,

            heap
        )

        if (

            len(heap) < k

            or

            abs(diff) < abs(heap[0][0])
        ):

            self._search(

                far_branch,

                query_vector,

                k,

                depth + 1,

                distance_function,

                heap
            )

    # =====================================
    # CLEAR
    # =====================================

    def clear(self):

        self.root = None

    # =====================================
    # REBUILD
    # =====================================

    def rebuild(self, items):

        self.clear()

        for item in items:

            self.insert(item)

    # =====================================
    # INFO
    # =====================================

    def info(self):

        return {

            "dims": self.dims,

            "has_root": self.root is not None
        }