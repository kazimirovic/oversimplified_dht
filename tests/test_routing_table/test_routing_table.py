import asynctest
from asynctest.mock import CoroutineMock, patch

from oversimplified_dht.node import Node
from oversimplified_dht.routing_table.bucket import Bucket
from oversimplified_dht.routing_table.table import RoutingTable
from ..mock_node import mock_node


class RoutingTableAddNodeTestCase(asynctest.TestCase):
    @patch("oversimplified_dht.routing_table.table.RoutingTable.MAXIMUM", 16)
    async def test_not_full(self):
        """bucket isn't full, node must be added straight away"""
        ping_function_mock = CoroutineMock()
        table = RoutingTable(1)

        added = await table.add_node(mock_node(8), ping_function_mock)
        self.assertTrue(added)
        ping_function_mock.assert_not_awaited()
        self.assertEqual(len(table.buckets), 1)
        self.assertEqual(len(table.buckets[0]), 1)

    @patch("oversimplified_dht.routing_table.table.RoutingTable.MAXIMUM", 16)
    async def test_full_with_our_id(self):
        """bucket is full of good nodes, our node_id within bucket's range, bucket must be split"""

        table = RoutingTable(1)
        table.buckets[0] = Bucket(RoutingTable.MINIMUM, RoutingTable.MAXIMUM,
                                  [mock_node(id_) for id_ in range(Bucket.MAX_NODES_NUMBER)])  # full bucket
        ping_function_mock = CoroutineMock()

        added = await table.add_node(mock_node(9), ping_function_mock)  # shall fall into the second bucket
        self.assertTrue(added)
        self.assertEqual(len(table.buckets), 2)

        index, bucket_with_our_node_id = table.get_bucket_for(table.node_id)
        second_bucket = table.buckets[
            len(table.buckets) - 1 - index]  # get the other bucket
        self.assertEqual(len(bucket_with_our_node_id), 8)
        self.assertEqual(len(second_bucket), 1)

    @patch("oversimplified_dht.routing_table.table.RoutingTable.MAXIMUM", 16)
    @patch("oversimplified_dht.routing_table.table.Bucket.MAX_NODES_NUMBER", 4)
    async def test_full(self):
        """bucket is full of good nodes, our node_id not within bucket's range, new node should be simply discarded"""
        ping_function_mock = CoroutineMock()
        table = RoutingTable(666)
        table.buckets[0] = Bucket(RoutingTable.MINIMUM, RoutingTable.MAXIMUM,
                                  [mock_node(id_) for id_ in range(Bucket.MAX_NODES_NUMBER)])  # full bucket

        added = await table.add_node(mock_node(id_=6), ping_function_mock)
        self.assertFalse(added)
        self.assertEqual(len(table.buckets), 1)
        ping_function_mock.assert_not_awaited()

    @patch("oversimplified_dht.routing_table.table.RoutingTable.MAXIMUM", 16)
    async def test_bad_nodes(self):
        """bucket is full but it has bad nodes, one of them should be replaced"""
        ping_function_mock = CoroutineMock()
        table = RoutingTable(666)
        table.buckets[0] = Bucket(RoutingTable.MINIMUM, RoutingTable.MAXIMUM,
                                  [mock_node(id_, Node.State.BAD) for id_ in
                                   range(Bucket.MAX_NODES_NUMBER)])  # full bucket
        added = await table.add_node(mock_node(id_=10), ping_function_mock)
        self.assertTrue(added)
        self.assertEqual(len(table.buckets), 1)
        ping_function_mock.assert_not_awaited()

    @patch("oversimplified_dht.routing_table.table.RoutingTable.MAXIMUM", 16)
    async def test_questionable_nodes(self):
        """bucket is full but it has questionable nodes, those should be pinged until one is bad"""
        ping_function_mock = CoroutineMock(return_value=False)
        table = RoutingTable(666)
        table.buckets[0] = Bucket(RoutingTable.MINIMUM, RoutingTable.MAXIMUM,
                                  [mock_node(id_, Node.State.QUESTIONABLE) for id_ in
                                   range(Bucket.MAX_NODES_NUMBER)])  # full bucket
        added = await table.add_node(mock_node(id_=15), ping_function_mock)
        self.assertTrue(added)
        self.assertEqual(len(table.buckets), 1)
        ping_function_mock.assert_awaited_once()
