import random
import socket
from crc32c import crc32 as crc32c
from os import urandom


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
    node_id[3:19] = urandom(17)
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
