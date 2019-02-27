import typing

from .node import Node
from .node_id import NodeId


class FlatRoutingTable:
    """
    This is a very inefficient routing table implementation. It doesn't use buckets as described in bep 0005.
    It doesn't do anything efficiently, actually.
    """
    MAX_NUMBER = 30

    def __init__(self, node_id: NodeId):
        self.nodes: typing.Dict[NodeId, Node] = {}
        self.node_id = node_id

    def get_neighbours(self, target_value: NodeId, k=8) -> typing.List[Node]:
        """

        :param target_value: can be a node id or an info hash
        :param k: number of nodes to return
        :return:
        """

        return sorted(self.nodes.values(), key=lambda node: node.info.id ^ target_value)

    async def add_node(self, new_node: Node, ping_function):
        """

        If the table is full of good nodes, the node is discarded
        If there's a bad or questionable node in the table, it is replaced.

        """

        if len(self.nodes) < self.MAX_NUMBER:
            self.nodes[new_node.id] = new_node
            return

        for node in self.nodes.values():
            status = node.get_status()
            if status != Node.State.GOOD:
                self.nodes.pop(node.id)
                self.nodes[new_node.id] = new_node
                break
