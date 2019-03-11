import asyncio
import logging
from math import inf
from typing import Callable, List, Awaitable

from oversimplified_dht.node import NodeInfo, Node, NodeId

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
logging.basicConfig()


class NodeCrawler:
    def __init__(self,
                 find_node_call: Callable[[Node, NodeId], Awaitable[List[NodeInfo]]],
                 nodes: List[Node],
                 target: NodeId, add_node_cb: Callable[[Node], None]):
        self.find_node = find_node_call
        self.target = target
        self.nodes = nodes
        self.add_node = add_node_cb
        self._best = inf

    def _better(self, value: NodeId):
        distance = self.target ^ value
        if distance < self._best:
            self._best = distance
            return True
        else:
            return False

    async def run(self):
        node_infos = await self.find_node(self.nodes[0], self.target)
        while True:
            new_node_infos = []
            requests = []
            nodes = []
            for info in node_infos:
                node = Node(info)
                requests.append(self.find_node(node, self.target))
                nodes.append(node)

            results = await asyncio.gather(*requests, return_exceptions=True)
            for r, node in zip(results, nodes):
                if isinstance(r, Exception):
                    if isinstance(r, asyncio.TimeoutError):
                        continue
                    if isinstance(r, KeyError):
                        continue
                    raise r
                self.add_node(node)

                new_node_infos += r

            log.debug('Got new node infos: %s' % node_infos)
            node_infos = sorted(new_node_infos, key=lambda x: x.id ^ self.target)[:8]
            if not node_infos:
                return
            if not self._better(node_infos[0].id):
                return
