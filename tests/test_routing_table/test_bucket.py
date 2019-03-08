import unittest

#from tests.dht.mock_node import MockNode

from oversimplified_dht.node import NodeId, Node, NodeInfo
from oversimplified_dht.routing_table.bucket import Bucket
#
#
# def get_filled_bucket(first_nodes_id, last_node_id, min_=None, max_=None, bucket=None, *args, **kwargs):
#     if bucket is None:
#         bucket = Bucket(min_, max_)
#     for i in range(first_nodes_id, last_node_id):
#         node = MockNode(id_=i, *args, **kwargs)
#         bucket.add_node(node)
#     return bucket
#
from tests.mock_node import mock_node


# class BucketTestCase(unittest.TestCase):
#     def test_split(self):
        # b = get_filled_bucket(0, 8, 0, 16)
        # b = Bucket(mock_node(id_) for id_ in range(Bucket.MAX_NODES_NUMBER-1))
        # nodes_to_first_bucket = b._nodes.values()
        # node_to_second_bucket = MockNode(id_=9)
        #
        # first, second = b.split(add_node=node_to_second_bucket)
        # self.assertIn(node_to_second_bucket.id, second)
        # self.assertNotIn(node_to_second_bucket.id, first)
        # for node in nodes_to_first_bucket:
        #     self.assertIn(node.id, first)
        #     self.assertNotIn(node.id, second)
    #
    # def test_split_discard_node(self):
    #     """If node passed to split() falls into the upper half of bucket's range, it should be discarded, one of the returned buckets should be empty"""
    #     b = get_filled_bucket(0, 8, 0, 18)
    #     nodes_to_first_bucket = b._nodes.values()
    #     node_to_be_discarded = MockNode(id_=9)
    #
    #     first, second = b.split(add_node=node_to_be_discarded)
    #     self.assertNotIn(node_to_be_discarded.id, second)
    #     self.assertNotIn(node_to_be_discarded.id, first)
    #     for node in nodes_to_first_bucket:
    #         self.assertIn(node.id, first)
    #         self.assertNotIn(node.id, second)
    #
    # def test_has_node_in_range(self):
    #     b = Bucket(0, 2)
    #     for i in range(0, 2):
    #         self.assertTrue(b.has_node_in_range(i))
    #     self.assertFalse(b.has_node_in_range(3))
    #
    # def test_full(self):
    #     b = get_filled_bucket(0, 8, 0, 8)
    #     print(b)
    #     self.assertTrue(b.full())
    #

if __name__ == '__main__':
    unittest.main()
