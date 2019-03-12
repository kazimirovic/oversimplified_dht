import asyncio
import logging
import typing
from typing import Sequence

from bencode.misc import unpack_compact_peer

from oversimplified_dht.bep42 import Bep42SecureIDManager
from oversimplified_dht.crawl import NodeCrawler, ValueCrawler
from oversimplified_dht.peer_storage import LocalPeerStorage
from oversimplified_dht.routing_table.table import RoutingTable
from oversimplified_dht.token_manager import TokenManager
from .krpc import KRPCProtocol
from .node import Node, parse_compact_nodes
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

    def requests_as_completed(self, nodes: Sequence[Node], method: bytes, args, timeout=TIMEOUT):
        return asyncio.as_completed(
            [self.send_query_to_node(node, method, args)
             for node in nodes],
            timeout=timeout
        )

    async def initial_bootstrap(self, target, bootstrap_nodes=DEFAULT_BOOTSTRAP_NODES) -> typing.List[Node]:
        """
        Returns a few nodes from bootstrap nodes. Ideally should only be called when we know of no other nodes at all
        :param bootstrap_nodes:
        :return:
        """
        request_args = {
            b'id': bytes(self.node_id),
            b'target': bytes(target)
        }
        for bootstrap_node_address in bootstrap_nodes:
            try:
                response = await self.send_query(bootstrap_node_address,
                                                 b'find_node', request_args)
                node_infos = parse_compact_nodes(response[b'r'][b'nodes'])
                return [Node(info) for info in node_infos]
            except asyncio.TimeoutError:
                log.warning("Bootstrap node %s not responding" % bootstrap_node_address[0])
        else:
            raise BootStrapError("No given boostrap nodes responded")

    async def get_neighbours(self, target: NodeId) -> typing.List[Node]:
        nodes = self.routing_table.get_neighbours(target)
        if nodes:
            return nodes
        return await self.initial_bootstrap(target)

    # noinspection PyTypeChecker
    async def bootstrap(self):
        log.debug('Begin bootstrap')
        c = NodeCrawler(self.call_find_node, nodes=await self.get_neighbours(self.node_id),
                        target=self.node_id,
                        add_node=self.add_node)
        await c.run()
        log.debug('Bootstrap done. %s' % self.routing_table)

    async def get_peers(self, info_hash: bytes):  # -> typing.Generator[Tuple[str, int], None, None]:
        target = NodeId.from_bytes(info_hash)
        c = ValueCrawler(self.call_find_peers, nodes=await self.get_neighbours(target),
                         target=target,
                         add_node=self.add_node)
        await c.run()
        return c.peers

    def add_node(self, new_node):
        asyncio.create_task(self.routing_table.add_node(new_node, ping_function=self.ping))

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
        return infos, None

    async def call_find_peers(self, node, target):
        response = await self.send_query_to_node(node, b'get_peers',
                                                 {b'id': bytes(self.node_id), b'info_hash': bytes(target)})
        try:
            r = response[b'r']
        except KeyError:
            log.debug('Invalid response: %s' % response)
            raise

        infos = parse_compact_nodes(r[b'nodes']) if b'nodes' in r else []
        if b'values' in r:
            peers = [unpack_compact_peer(p) for p in r[b'values']]
        else:
            peers=None

        return infos, peers
