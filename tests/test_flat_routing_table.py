import asynctest
from asynctest import mock
from asynctest.mock import MagicMock, CoroutineMock

from oversimplified_dht.node import Node, NodeInfo
from oversimplified_dht.node_id import NodeId
from oversimplified_dht.routing_table import FlatRoutingTable

last_id = 0


def mock_node(state, id_):
    n = Node(NodeInfo('127.0.0.1', 666, id_))
    n.get_status = MagicMock(return_value=state)
    return n


class FlatRoutingTableTestCase(asynctest.TestCase):
    # noinspection PyAttributeOutsideInit
    def setUp(self):
        self.ping = CoroutineMock()

    @mock.patch('oversimplified_dht.routing_table.FlatRoutingTable.MAX_NUMBER', 3)
    async def test_add_node(self):
        t = FlatRoutingTable(NodeId.from_int(0))

        for i in range(FlatRoutingTable.MAX_NUMBER + 1):
            await t.add_node(mock_node(Node.State.GOOD, NodeId.from_int(i)), ping_function=self.ping)
        self.assertEqual(len(t.nodes), t.MAX_NUMBER)

    @mock.patch('oversimplified_dht.routing_table.FlatRoutingTable.MAX_NUMBER', 3)
    async def test_get_neighbours(self):
        t = FlatRoutingTable(NodeId.from_int(0))

        for i in range(FlatRoutingTable.MAX_NUMBER + 1):
            await t.add_node(mock_node(Node.State.GOOD, NodeId.from_int(i)), ping_function=self.ping)
        result = t.get_neighbours(t.node_id, 2)
        resulting_ids = [int(node.info.id) for node in result]
        self.assertIn(0, resulting_ids)
        self.assertIn(2, resulting_ids)
        self.assertNotIn(3, resulting_ids)


if __name__ == '__main__':
    asynctest.main()
