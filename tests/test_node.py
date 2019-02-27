import unittest

from oversimplified_dht.node import *

parsed = [
    NodeInfo(host='89.18.156.75', port=24871, id=NodeId.from_int(395393348061665137205962901399654523754872955706)),
    NodeInfo(host='182.73.241.246', port=49526, id=NodeId.from_int(444335964268689435626828838813143706981015465660)),
    NodeInfo(host='46.166.88.186', port=1030, id=NodeId.from_int(1405519151050532776101252275778280610035504856682)),
]

raw = b"EB\r\t\x7f|\x92\x9aV\x98\xa4{\xb3\xc2\xa70\x9a=\xe3:Y\x12\x9cK\
a'M\xd4\xb6\xb7\xa9\x9c\x96\x10f\x01\x88\x99\x03\x93f7\x07\x7f\xae\xbc\xb6I\xf1\xf6\xc1v\xf61\xa8\x93\x14\xc2\xc0\xf9\xa1\x1d;\xf2~\xdc\xfa\
L\x0eu>j.\xa6X\xba\x04\x06"


class CompactNodeTestCase(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_compact_nodes(raw), parsed)

    def test_pack(self):
        self.assertEqual(pack_compact_nodes(parsed), raw)
