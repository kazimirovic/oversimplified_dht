import asyncio
import heapq
import operator
from itertools import chain
from typing import Tuple, List

from .bucket import Bucket
from ..node import Node
from ..node_id import NodeId


class TableTraverser:
    def __init__(self, table, node_id):
        index, bucket = table.get_bucket_for(node_id)
        # table.buckets[index].touchLastUpdated()
        self.currentNodes = table.buckets[index].get_nodes_list()
        self.leftBuckets = table.buckets[:index]
        self.rightBuckets = table.buckets[(index + 1):]
        self.left = True

    def __iter__(self):
        return self

    def __next__(self):
        """
        Pop an item from the left subtree, then right, then left, etc.
        """
        if len(self.currentNodes) > 0:
            return self.currentNodes.pop()

        if self.left and len(self.leftBuckets) > 0:
            self.currentNodes = self.leftBuckets.pop().get_nodes_list()
            self.left = False
            return next(self)

        if len(self.rightBuckets) > 0:
            self.currentNodes = self.rightBuckets.pop(0).get_nodes_list()
            self.left = True
            return next(self)

        raise StopIteration


class RoutingTable:
    MINIMUM = 0
    MAXIMUM = 2 ** 160

    def __init__(self, node_id):
        self.buckets = [Bucket(min_=self.MINIMUM, max_=self.MAXIMUM)]
        self.node_id = node_id
        self.lock = asyncio.Lock()

    def get_neighbours(self, node_id: NodeId, k=8) -> List[Node]:
        nodes = []
        for node in TableTraverser(self, node_id):
            heapq.heappush(nodes, (node_id ^ node.id, node))
            # nodes.append(node)
            if len(nodes) == k:
                break

        return list(map(operator.itemgetter(1), heapq.nsmallest(k, nodes)))

    def split_bucket(self, index, add_node: Node):
        b = self.buckets[index]
        middle_point = (b.max + b.min) // 2
        first = Bucket(b.min, middle_point)
        second = Bucket(middle_point, b.max)

        for node in chain(b.get_nodes_list(), [add_node]):
            bucket = first if int(node.id) < middle_point else second
            if not bucket.full():
                bucket.add_node(node)
        self.buckets[index] = first
        self.buckets.insert(index + 1, second)
        return first, second

    def get_bucket_for(self, node_id: NodeId) -> Tuple[int, Bucket]:
        for index, bucket in enumerate(self.buckets):
            if bucket.has_id_in_range(node_id):
                return index, bucket

        raise ValueError("No bucket has node id %i in range " % node_id)

    async def add_node(self, node: Node, ping_function) -> bool:
        """
        :param node: node to add
        :param ping_function: returns True if node responds, otherwise False.
        :return: True if node was added, False if it was discarded
        """
        questionable_nodes = []
        bucket_index, bucket = self.get_bucket_for(node.id)

        if node.id in bucket:
            return False

        if not bucket.full():
            bucket.add_node(node)
            return True

        if bucket.has_id_in_range(self.node_id):
            self.split_bucket(bucket_index, node)
            return True

        for current_node in bucket:
            if current_node.get_status() == Node.State.BAD:
                bucket.replace_node(current_node.id, node)
                return True
            if current_node.get_status() == Node.State.QUESTIONABLE:
                questionable_nodes.append(current_node)

        questionable_nodes.sort(key=lambda n: n.last_interaction)

        # If any nodes are questionable, they are pinged beginning from the least recently pinged one
        for questionable_node in questionable_nodes:
            node_responds = await ping_function()
            if node_responds:
                bucket.update_last_changed()
            else:
                bucket.replace_node(questionable_node.id, node)
                return True
        return False

    def __repr__(self):
        return "<RoutingTable: %s>" % ','.join(str(len(bucket)) for bucket in self.buckets)
