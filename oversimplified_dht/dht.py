import asyncio
import logging
import typing
from typing import Sequence, Tuple

from bencode.misc import unpack_compact_peer

from oversimplified_dht.bep42 import Bep42SecureIDManager
from oversimplified_dht.crawl import NodeCrawler
from oversimplified_dht.peer_storage import LocalPeerStorage
from oversimplified_dht.routing_table.table import RoutingTable
from oversimplified_dht.token_manager import TokenManager
from .krpc import KRPCProtocol
from .node import Node, parse_compact_nodes, NodeInfo
from .node_id import NodeId

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
logging.basicConfig()


class BootStrapError(Exception):
    pass


class NodeIdChanged(Exception):
    pass


class Router(KRPCProtocol):
    DEFAULT_BOOTSTRAP_NODES = (('router.utorrent.com', 6881),)
    TIMEOUT = 1

    async def get_peers(self, info_hash: bytes) -> typing.Generator[Tuple[str, int], None, None]:
        """
        Yields peer infos as they are found. Stops when no nodes closer to info_hash can be found.

        Iteratively query nodes that are closer to info_hash until it cannot find any closer nodes
        :param info_hash:
        :return:
        """

        info_hash = NodeId.from_bytes(info_hash)
        nodes = self.routing_table.get_neighbours(info_hash)
        if not nodes:
            raise ValueError('Routing tables returned no nodes')

        peers = set()  # we don't want to return duplicates
        request_args = {b'id': bytes(self.node_id), b'info_hash': bytes(info_hash)}

        best = info_hash ^ self.node_id
        found_better = True
        while found_better:
            found_better = False
            node_infos = []
            for request, node in zip(self.requests_as_completed(nodes, b'get_peers', request_args, timeout=6), nodes):
                try:
                    # noinspection PyUnresolvedReferences
                    response = await request
                except asyncio.TimeoutError:
                    continue
                if b'e' in response:
                    log.debug('Got error response: %s' % str(response))
                    continue
                if b'r' not in response:
                    log.debug('Got bad response to "get_peers": %s' % str(response))
                    continue
                if b'values' in response[b'r']:
                    await self.add_node(node)
                    for compact_peer_info in response[b'r'][b'values']:
                        peer_info = unpack_compact_peer(compact_peer_info)
                        if peer_info not in peers:
                            peers.add(peer_info)
                            yield peer_info

                elif b'nodes' in response[b'r']:
                    await self.add_node(node)
                    node_infos += parse_compact_nodes(response[b'r'][b'nodes'])
                else:
                    log.debug('Got bad response to "get_peers": ', response)
                    continue
                distance = node.id ^ self.node_id
                if distance < best:
                    best = distance
                    found_better = True

            node_infos.sort(key=lambda x: x.id ^ info_hash)  # closest first
            logging.debug('Got new node infos:%s' % node_infos)
            nodes = [Node(node_info) for node_info in node_infos]

    def requests_as_completed(self, nodes: Sequence[Node], method: bytes, args, timeout=TIMEOUT):
        return asyncio.as_completed(
            [self.send_query_to_node(node, method, args)
             for node in nodes],
            timeout=timeout
        )

    # noinspection PyTypeChecker
    async def bootstrap(self):
        log.debug('Begin bootstrap')
        c = NodeCrawler(self.call_find_node, nodes=[Node(NodeInfo('router.utorrent.com', 6881, None))],
                        target=self.node_id,
                        add_node_cb=lambda node: asyncio.create_task(self.add_node(node)))
        await c.run()
        log.debug('Bootstrap done. %s' % self.routing_table)

    async def add_node(self, new_node):
        await self.routing_table.add_node(new_node, ping_function=self.ping)

    async def ping(self, node):
        return await self.send_query_to_node(node, b'ping', args={b'id': bytes(self.node_id)})

    # noinspection PyMethodOverriding
    @classmethod
    async def create(cls, node_id, port=49001) -> 'Router':
        _, protocol = await asyncio.get_running_loop().create_datagram_endpoint(lambda: cls(node_id),
                                                                                local_addr=('0.0.0.0', port))
        # noinspection PyTypeChecker
        return protocol

    # noinspection PyUnusedLocal
    def krpc_handle_ping(self, request, address):
        return self.response(request, {b'id': bytes(self.node_id), })

    def __init__(self, node_id: NodeId):
        super().__init__()
        self.node_id = node_id
        self.secure_id_manager = Bep42SecureIDManager()
        self.peer_storage = LocalPeerStorage()
        self.routing_table = RoutingTable(self.node_id)
        self.token_manager = TokenManager()

    async def send_query_to_node(self, node: Node, method: bytes, args: dict):
        """
        Sends query to node. Raises TimeoutError if the node fails to respond in time defined by TIMEOUT.
        :param node:
        :param method: e.g. b'ping'
        :param args:  e.g. {b'id':self.node_id.to_bytes()}
        :return:
        """
        try:
            response = await asyncio.wait_for(self.send_query((node.info.host, node.info.port), method, args),
                                              self.TIMEOUT)
        except asyncio.TimeoutError:
            node.record_not_responding()
            raise
        else:
            node.record_responded()
            if b'ip' in response:
                node_id = self.secure_id_manager.record_ip(unpack_compact_peer(response[b'ip'])[0])
                if node_id is not None:
                    self.change_id(node_id)

            return response

    def change_id(self, node_id: NodeId):
        """
        Changes id to :param node_id: and creates a new routing table.
        IDEA: reuse known nodes from the old routing table maybe?
        :return:
        """
        self.node_id = node_id
        self.routing_table = RoutingTable(node_id)

    async def call_find_node(self, node, target):
        response = await self.send_query_to_node(node, b'find_node',
                                                 {b'id': bytes(self.node_id), b'target': bytes(target)})
        try:
            infos = parse_compact_nodes(response[b'r'][b'nodes'])
        except KeyError:
            log.debug('Invalid response: %s' % response)
            raise
        return infos
