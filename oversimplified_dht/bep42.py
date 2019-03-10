import random
import socket
from crc32c import crc32 as crc32c
from os import urandom

from .node_id import NodeId


class Bep42SecureIDManager:
    VOTES_NEEDED = 2

    def __init__(self):
        """
        When the number of nodes that responded with the same ip parameters exceedes VOTES_NEEDED,
        will call change_id_cb.
        :param change_id_cb:
        """
        self.ip = None
        self.number_votes = 0

    def record_ip(self, ip):
        """

        :param ip:
        :return: NodeId if id needs changing, otherwise None
        """
        if ip == self.ip:
            if self.number_votes < self.VOTES_NEEDED:
                self.number_votes += 1
                if self.number_votes >= self.VOTES_NEEDED:
                    node_id = NodeId.from_bytes(gen_id(self.ip, random.randint(0, 100)))
                    print('Restarting node, our new ip is %s and our new id is %s' % (self.ip, node_id))
                    return node_id
        else:
            self.ip = ip
            self.number_votes = 0

    @staticmethod
    def verify(ip, node_id: NodeId):
        verify_id(ip, bytes(node_id))


def gen_id(ip: str, rand: int):
    ip = bytearray(socket.inet_aton(ip))
    r = rand & 0x7
    mask = [0x03, 0x0f, 0x3f, 0xff]
    for i in range(4):
        ip[i] &= mask[i]
    ip[0] |= r << 5
    crc = crc32c(ip)
    node_id = bytearray(20)
    node_id[0] = (crc >> 24) & 0xff
    node_id[1] = (crc >> 16) & 0xff
    node_id[2] = ((crc >> 8) & 0xf8) | random.randint(0, 7)
    node_id[3:19] = urandom(16)
    node_id[19] = rand
    return bytes(node_id)


def verify_id(ip: str, node_id: bytes):
    ip = bytearray(socket.inet_aton(ip))
    rand = node_id[19]
    r = rand & 0x7
    mask = [0x03, 0x0f, 0x3f, 0xff]
    for i in range(4):
        ip[i] &= mask[i]
    ip[0] |= r << 5
    crc = crc32c(ip)
    return (node_id[0] == (crc >> 24) & 0xff and
            node_id[1] == (crc >> 16) & 0xff and
            node_id[2] & 0xf8 == ((crc >> 8) & 0xf8) and
            node_id[19] == rand)
