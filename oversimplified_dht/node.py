import datetime
import typing
from dataclasses import dataclass
from enum import Enum

from bencode.misc import pack_compact_peer, unpack_compact_peer, group

from .node_id import NodeId


@dataclass
class NodeAddress:
    host: str
    port: int


@dataclass
class NodeInfo:
    host: str
    port: int
    id: NodeId


class Node:
    """
    Keeps node's info as well as its 'reputation'.
    To keep track of the latter:
    record_responded must be called whenever we receive as a valid response from the node
    record_not_responding - whenever our query times out
    record_queried - whenever we receive a query from the node

    >>> n= Node(NodeInfo('127.0.0.1', 666, NodeId.from_int(1)))
    >>> n.get_status()
    <NodeState.BAD: 2>
    >>> n.record_responded()
    >>> n.get_status()
    <NodeState.GOOD: 1>
    >>> n= Node(NodeInfo('127.0.0.1', 666, NodeId.from_int(1)))
    >>> n.record_responded(datetime.datetime.now()-datetime.timedelta(minutes=16))
    >>> n.get_status()
    <NodeState.QUESTIONABLE: 3>

    """
    # noinspection PyArgumentList
    State = Enum('NodeState', 'GOOD BAD QUESTIONABLE')
    MAX_QUERIES_WITHOUT_RESPONSE = 2  # once reached, Node becomes BAD
    INACTIVE_TIMEOUT = datetime.timedelta(minutes=15)

    def __init__(self, node_info: NodeInfo):
        self.info = node_info
        self.last_interaction = None  # None until we receive a response from the node
        self.queries_not_responded = 0  # queries not responded in a row
        self.last_response = None

    def record_responded(self, time=None):
        self.last_response = self.last_interaction = datetime.datetime.now() if time is None else time
        self.queries_not_responded = 0

    def record_queried(self, time=None):
        if self.last_interaction is not None:
            self.last_interaction = datetime.datetime.now() if time is None else time

    def record_not_responding(self):
        self.queries_not_responded += 1

    def get_status(self):
        if self.last_interaction is None:
            return Node.State.BAD
        if self.queries_not_responded > self.MAX_QUERIES_WITHOUT_RESPONSE:
            return Node.State.BAD
        if datetime.datetime.now() - self.last_interaction > self.INACTIVE_TIMEOUT:
            return Node.State.QUESTIONABLE

        return Node.State.GOOD

    @property
    def id(self):
        return self.info.id

    def __repr__(self):
        return "%s Node(host=%s, port=%i, id=%i)" % (
            self.get_status().name, self.info.host, self.info.port, int(self.info.id))


def parse_compact_nodes(data: bytes) -> typing.List[NodeInfo]:
    node_infos = []
    for data in group(data, 26):
        ip, port = unpack_compact_peer(data[20:])
        node_id = NodeId.from_bytes(data[:20])
        node_infos.append(NodeInfo(ip, port, node_id))
    return node_infos


def pack_compact_nodes(nodes_list: typing.List[NodeInfo]) -> bytes:
    return b''.join(bytes(node_info.id) + pack_compact_peer(node_info.host, node_info.port) for node_info in nodes_list)
