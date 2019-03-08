import datetime
from itertools import chain
from typing import Dict
from typing import List

from ..node import Node
from ..node_id import NodeId


class Bucket:
    MAX_NODES_NUMBER = 8

    def __init__(self, min_: int = 0, max_: int = 2 ** 160, nodes=None):
        self.min = min_
        self.max = max_
        self._nodes: Dict[NodeId, Node] = {}
        self.last_changed = datetime.datetime.now()
        if nodes is not None:
            for node in nodes:
                self._nodes[node.id] = node

    def __iter__(self):
        return iter(self._nodes.values())

    def get_nodes_list(self) -> List[Node]:
        return list(self._nodes.values())

    def __len__(self):
        return len(self._nodes)

    def __contains__(self, node_id: int):
        return node_id in self._nodes

    def has_id_in_range(self, node_id: NodeId):
        """
        >>> b=Bucket(0,2)
        >>> b.has_id_in_range(NodeId.from_int(0))
        True
        >>> b.has_id_in_range(NodeId.from_int(1))
        True
        >>> b.has_id_in_range(NodeId.from_int(2))
        False

        :param node_id:
        :return:
        """
        return self.min <= int(node_id) < self.max

    def fresh(self):
        now = datetime.datetime.now()
        if now - self.last_changed > datetime.timedelta(minutes=15):
            for node in self._nodes.values():
                if now - node.last_response > datetime.timedelta(minutes=15):
                    return True
        return False

    def add_node(self, node: Node):
        self._nodes[node.id] = node
        assert len(self._nodes) <= self.MAX_NODES_NUMBER
        self.update_last_changed()

    def pop_node(self, node_id: NodeId):
        return self._nodes.pop(node_id)

    def replace_node(self, ex_id: NodeId, node):
        self.pop_node(ex_id)
        self.add_node(node)

    def update_last_changed(self):
        self.last_changed = datetime.datetime.now()

    def split(self):
        middle_point = (self.max + self.min) // 2
        first = Bucket(self.min, middle_point)
        second = Bucket(middle_point, self.max)
        for node in chain(self._nodes.values(), [add_node]):
            bucket = first if node.id <= middle_point else second
            if not bucket.full():
                bucket.add_node(node)
        return first, second

    def full(self):
        return len(self._nodes) >= self.MAX_NODES_NUMBER

    def __repr__(self):
        return "Bucket [%i-%i] containing %i items" % (self.min, self.max, len(self._nodes))
