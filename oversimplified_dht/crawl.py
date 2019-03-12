import asyncio
import logging
from math import inf
from typing import Callable, List, Tuple, Any

from oversimplified_dht.node import Node, NodeId

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
logging.basicConfig()


class NodeCrawler:
    def __init__(self, rpc_find, nodes: List[Node], target: NodeId, add_node: Callable[[Node], None]):
        self.rpc_find = rpc_find
        self.nodes = nodes
        self.target = target
        self.add_node = add_node
        self._best = inf

    def found_peers(self, peer_infos: List[Tuple[Any]]):
        """
        Called when peer infos are encountered
        :param peer_infos:
        :return:
        """

    async def run(self):
        while True:
            node_infos = []
            results = await asyncio.gather(*(
                self.rpc_find(node, self.target) for node in self.nodes
            ), return_exceptions=True)

            for r, node in zip(results, self.nodes):
                if isinstance(r, Exception):
                    if isinstance(r, (asyncio.TimeoutError, KeyError)):
                        continue
                    raise r

                self.add_node(node)

                new_node_infos, peer_infos = r
                if peer_infos:
                    self.found_peers(peer_infos)

                node_infos += new_node_infos

            log.debug('Got new node infos: %s' % node_infos)
            node_infos = sorted(node_infos, key=lambda x: x.id ^ self.target)[:8]
            if not node_infos:
                return
            if not self._better(node_infos[0].id):
                return
            self.nodes = [Node(info) for info in node_infos]

    def _better(self, value: NodeId):
        distance = self.target ^ value
        if distance < self._best:
            self._best = distance
            return True
        else:
            return False


class ValueCrawler(NodeCrawler):
    def __init__(self, rpc_find, nodes: List[Node], target: NodeId, add_node: Callable[[Node], None]):
        super().__init__(rpc_find, nodes, target, add_node)
        self.peers = []

    def found_peers(self, peer_infos: List[Tuple]):
        self.peers.append(peer_infos)
