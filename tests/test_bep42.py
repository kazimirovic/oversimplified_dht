import unittest
from functools import partial
from operator import is_not

from oversimplified_dht import bep42


class Bep42TestCase(unittest.TestCase):
    def test_gen_id(self):
        data = (
            ("124.31.75.21", 1, (0x5f, 0xbf, 0xbf)),
            ("21.75.31.124", 86, (0x5a, 0x3c, 0xe9)),
            ("65.23.51.170", 22, (0xa5, 0xd4, 0x32)),
            ("84.124.73.14", 65, (0x1b, 0x03, 0x21)),
            ("43.213.53.83", 90, (0xe5, 0x6f, 0x6c))
        )

        for ip, rand, prefixes in data:
            id_ = bep42.gen_id(ip, rand)
            self.assertEqual(id_[0], prefixes[0])
            self.assertEqual(id_[1], prefixes[1])
            self.assertEqual(id_[2] & 0xf8, prefixes[2] & 0xf8)
            self.assertEqual(id_[19], rand)

            self.assertEqual(len(id_), 20)

    def test_verify_id(self):
        data = (
            ("124.31.75.21", b'_\xbf\xbd\x03m\x1b\x85cY\x0b\x0e\xb5\x8d.\x96\xefV\xedN\x01\x00'),
            ("21.75.31.124", b'Z<\xeas\xaf\xa5)\nP\xc8\xa1\xb0a\xcc\xba\xe9\x0e\x91\x02V\x00'),
            ("65.23.51.170", b'\xa5\xd46\xc5\xde\x8f\x08L\xffE\xbd\xe3=\x84$\x93\xcdb\xef\x16\x00'),
            ("84.124.73.14", b'\x1b\x03"_ \xaf\xc8dI\xb7\xca\r\x00D\x7f\xcc+\xbb(A\x00'),
            ("43.213.53.83", b'\xe5ol|$\xe0t\xd7]\xddV\x8b\xa0\xdb[x\x19\xc7AZ\x00')
        )
        for ip, node_id in data:
            self.assertTrue(bep42.verify_id(ip, node_id), '%s not ok with %s' % (ip, node_id))


class SecureIDManagerTestCase(unittest.TestCase):
    def test(self):
        s = bep42.Bep42SecureIDManager()
        self.assertEqual(
            len(
                list(filter(partial(is_not, None),
                            (s.record_ip('127.0.0.1') for _ in range(s.VOTES_NEEDED * 2))
                            )
                     )
            ),
            1
        )


if __name__ == '__main__':
    unittest.main()
