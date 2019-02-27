import asyncio
from unittest.mock import MagicMock

import asynctest
import bencode as b

from oversimplified_dht.krpc import KRPCProtocol


class MockServerProtocol(asyncio.DatagramProtocol):
    transport: asyncio.DatagramTransport

    def __init__(self, sleep_time: int, reply_after: int, address):
        self.sleep_time = sleep_time
        self.received = 0
        self.address = address
        self.reply_after = reply_after

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, datagram, address):
        self.received += 1
        if self.received >= self.reply_after:
            decoded = b.decode(datagram)
            data = b.encode({b't': decoded[b't'], b'y': b'r', b'a': b''})
            asyncio.get_running_loop().call_later(self.sleep_time, lambda: self.reply(address, data))

    def reply(self, address, data):
        self.transport.sendto(addr=address, data=data)

    @classmethod
    async def create(cls, sleep_time, reply_after, port=9999):
        address = ('127.0.0.1', port)
        transport, protocol = await asyncio.get_running_loop().create_datagram_endpoint(
            lambda: cls(sleep_time, reply_after, address),
            local_addr=address)
        return protocol


class KRPCTestCase(asynctest.TestCase):
    async def setUp(self):
        # noinspection PyAttributeOutsideInit
        self.krpc = await KRPCProtocol.create()

    async def test_rpc(self):
        krpc2 = await KRPCProtocol.create(port=49003)
        krpc2.krpc_handle_test = MagicMock(return_value=b.encode({b't': b'\x00\x00', b'y': b'r'}))
        krpc2_address = ('127.0.0.1', 49003)

        await self.krpc.send_query(krpc2_address, b'test', args={1: 2})
        krpc2.krpc_handle_test.assert_called()
        self.assertEqual(self.krpc.last_transaction_id, 1)
        self.assertFalse(self.krpc.transactions)

    async def test_timeout(self):
        node1 = self.krpc
        mock_server: MockServerProtocol = await MockServerProtocol.create(1, 0)
        # noinspection PyAsyncCall

        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(node1.send_query(mock_server.address, b'test', {}), 0.1)
        self.assertFalse(node1.transactions)

        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(node1.send_query(mock_server.address, b'test', {}), 1)
        self.assertFalse(node1.transactions)


if __name__ == '__main__':
    asynctest.main()
