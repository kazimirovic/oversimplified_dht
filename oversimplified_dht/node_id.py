class NodeId:
    """

    >>> bytes(NodeId.from_int(1))
    b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x01'

    >>> int(NodeId.from_bytes(
    ... b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x01'))
    1

    >>> NodeId.from_int(1)
    NodeId(1)

    >>> NodeId.from_int(1) == NodeId.from_int(1)
    True

    >>> NodeId.from_int(1)^NodeId.from_int(2)
    3
    """

    __slots__ = ['id_bytes', 'id_int']

    def __xor__(self, other):
        return int(self) ^ int(other)

    def __bytes__(self):
        return self.id_bytes

    def __int__(self):
        return self.id_int

    @classmethod
    def from_bytes(cls, data: bytes):
        return cls(data, cls.bytes_to_int(data))

    @classmethod
    def from_int(cls, data: int):
        return cls(cls.int_to_bytes(data), data)

    @staticmethod
    def bytes_to_int(data: bytes) -> int:
        return int(data.hex(), 16)

    @staticmethod
    def int_to_bytes(data: int) -> bytes:
        return data.to_bytes(byteorder='big', length=20)

    def __init__(self, bytes_data, int_data):
        self.id_bytes = bytes_data
        self.id_int = int_data

    def __hash__(self):
        return hash(self.id_bytes)

    def __repr__(self):
        return "NodeId(%i)" % int(self)

    def __eq__(self, other):
        return int(self) == int(other)
