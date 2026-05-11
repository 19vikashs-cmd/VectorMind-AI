import math
import random
import heapq

from metrics.metrics import get_distance_function


class HNSWGraphNode:

    def __init__(
        self,
        item,
        level
    ):

        self.item = item

        self.level = level

        self.neighbors = [
            [] for _ in range(level + 1)
        ]


class HNSWIndex:

    def __init__(
        self,
        m=16,
        ef_construction=200
    ):

        self.m = m

        self.m0 = m * 2

        self.ef_construction = ef_construction

        self.level_mult = 1 / math.log(m)

        self.nodes = {}

        self.entry_point = None

        self.top_layer = -1

        random.seed(42)

    # =====================================
    # RANDOM LEVEL
    # =====================================

    def random_level(self):

        r = random.random()

        return int(
            math.floor(
                -math.log(r) * self.level_mult
            )
        )

    # =====================================
    # SEARCH LAYER
    # =====================================

    def search_layer(
        self,
        query_vector,
        entry_id,
        ef,
        layer,
        distance_function
    ):

        visited = set()

        candidates = []

        found = []

        dist = distance_function(
            query_vector,
            self.nodes[entry_id].item["embedding"]
        )

        heapq.heappush(
            candidates,
            (dist, entry_id)
        )

        heapq.heappush(
            found,
            (-dist, entry_id)
        )

        visited.add(entry_id)

        while candidates:

            current_dist, current_id = heapq.heappop(
                candidates
            )

            worst_found = -found[0][0]

            if (
                len(found) >= ef
                and current_dist > worst_found
            ):
                break

            node = self.nodes[current_id]

            if layer >= len(node.neighbors):
                continue

            for neighbor_id in node.neighbors[layer]:

                if neighbor_id in visited:
                    continue

                visited.add(neighbor_id)

                neighbor_node = self.nodes[neighbor_id]

                d = distance_function(
                    query_vector,
                    neighbor_node.item["embedding"]
                )

                if (
                    len(found) < ef
                    or d < worst_found
                ):

                    heapq.heappush(
                        candidates,
                        (d, neighbor_id)
                    )

                    heapq.heappush(
                        found,
                        (-d, neighbor_id)
                    )

                    if len(found) > ef:
                        heapq.heappop(found)

        results = []

        while found:

            neg_dist, node_id = heapq.heappop(found)

            item = self.nodes[node_id].item

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
                    -neg_dist,
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

        return results

    # =====================================
    # INSERT
    # =====================================

    def insert(self, item):

        node_id = item["id"]

        level = self.random_level()

        new_node = HNSWGraphNode(
            item,
            level
        )

        self.nodes[node_id] = new_node

        if self.entry_point is None:

            self.entry_point = node_id

            self.top_layer = level

            return

        current_entry = self.entry_point

        distance_function = get_distance_function(
            "cosine"
        )

        for layer in range(
            self.top_layer,
            level,
            -1
        ):

            results = self.search_layer(
                item["embedding"],
                current_entry,
                1,
                layer,
                distance_function
            )

            if results:
                current_entry = results[0]["id"]

        for layer in range(
            min(level, self.top_layer),
            -1,
            -1
        ):

            neighbors = self.search_layer(
                item["embedding"],
                current_entry,
                self.ef_construction,
                layer,
                distance_function
            )

            max_neighbors = (
                self.m0 if layer == 0
                else self.m
            )

            selected = neighbors[:max_neighbors]

            for n in selected:

                nid = n["id"]

                new_node.neighbors[layer].append(
                    nid
                )

                neighbor_node = self.nodes[nid]

                while (
                    len(neighbor_node.neighbors)
                    <= layer
                ):
                    neighbor_node.neighbors.append([])

                neighbor_node.neighbors[layer].append(
                    node_id
                )

                if (
                    len(neighbor_node.neighbors[layer])
                    > max_neighbors
                ):

                    scored = []

                    for other_id in neighbor_node.neighbors[layer]:

                        d = distance_function(
                            neighbor_node.item["embedding"],
                            self.nodes[other_id].item["embedding"]
                        )

                        scored.append(
                            (d, other_id)
                        )

                    scored.sort(
                        key=lambda x: x[0]
                    )

                    neighbor_node.neighbors[layer] = [

                        oid

                        for _, oid in scored[:max_neighbors]
                    ]

            if neighbors:
                current_entry = neighbors[0]["id"]

        if level > self.top_layer:

            self.top_layer = level

            self.entry_point = node_id

    # =====================================
    # SEARCH
    # =====================================

    def search(
        self,
        query_vector,
        k=3,
        ef=50,
        metric="cosine",
        distance_function=None
    ):

        if self.entry_point is None:
            return []

        if distance_function is None:

            distance_function = get_distance_function(
                metric
            )

        current = self.entry_point

        for layer in range(
            self.top_layer,
            0,
            -1
        ):

            results = self.search_layer(
                query_vector,
                current,
                1,
                layer,
                distance_function
            )

            if results:
                current = results[0]["id"]

        results = self.search_layer(
            query_vector,
            current,
            max(k, ef),
            0,
            distance_function
        )

        return results[:k]

    # =====================================
    # REMOVE
    # =====================================

    def remove(self, node_id):

        if node_id not in self.nodes:
            return False

        for other_node in self.nodes.values():

            for layer in other_node.neighbors:

                if node_id in layer:
                    layer.remove(node_id)

        del self.nodes[node_id]

        if self.entry_point == node_id:

            self.entry_point = None

            self.top_layer = -1

            for nid, node in self.nodes.items():

                self.entry_point = nid

                self.top_layer = node.level

                break

        return True

    # =====================================
    # CLEAR
    # =====================================

    def clear(self):

        self.nodes = {}

        self.entry_point = None

        self.top_layer = -1

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

    def get_graph_info(self):

        return {

            "node_count": len(self.nodes),

            "top_layer": self.top_layer,

            "entry_point": self.entry_point
        }

    # =====================================
    # INFO ALIAS
    # =====================================

    def info(self):

        return self.get_graph_info()