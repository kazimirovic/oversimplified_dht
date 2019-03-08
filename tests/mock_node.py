import datetime

from asynctest.mock import MagicMock

from oversimplified_dht import NodeId
from oversimplified_dht.node import Node, NodeInfo


def mock_node(id_, state=Node.State.GOOD):
    if isinstance(id_, int):
        id_ = NodeId.from_int(id_)
    n = Node(NodeInfo('127.0.0.1', 666, id_))
    n.last_interaction = datetime.datetime.now()
    n.get_status = MagicMock(return_value=state)
    return n
