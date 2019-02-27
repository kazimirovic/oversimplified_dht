import asyncio
import logging
from functools import partialmethod

import bencode as b

log = logging.getLogger(__name__)


class KRPCProtocol(asyncio.DatagramProtocol):
    @classmethod
    async def create(cls, port=49001) -> 'KRPCProtocol':
        _, protocol = await asyncio.get_running_loop().create_datagram_endpoint(cls, local_addr=('0.0.0.0', port))
        # noinspection PyTypeChecker
        return protocol

    @staticmethod
    def response(request, args):
        """
        Helper method to form responses. Can be used in query handlers
        :param request: decoded request
        :param args: response args
        :return: ready-to-send response body
        """
        return b.encode({b'y': b'r', b't': request[b't'], b'r': args})

    @staticmethod
    def error(request, code, description):
        """
        Helper method to form error responses, Can be used in query handlers
        :param request: decoded request
        :param code: error code
        :param description: error description
        :return: ready-to-send response body
        """
        return b.encode({b'y': b'e', b't': request[b't'], b'e': [code, description]})

    error_generic = partialmethod(error, code=201, description=b'Generic Error')
    error_server = partialmethod(error, code=202, description=b'Server Error')
    error_protocol = partialmethod(error, code=203, description=b'Protocol Error')
    error_method_unknown = partialmethod(error, code=204, description=b'Method Unknown')
    error_invalid_arguments = partialmethod(error, code=203, description=b'Invalid arguments')

    async def send_query(self, addr, method: bytes, args: dict):
        """
        :param addr: (ip,port) as passed to transport send_to
        :param method: method name byte string, e.g. b'get_peers'
        :param args: arguments to the query, e.g.  {"id": "<querying nodes id>", "info_hash": "<info hash of target torrent>"}
        :return: whole node's response like {"t":"aa", "y":"r", "r": {"id":"<queried nodes id>", "values":["<value1>",]}}
                 Response may also be error like {"t":"aa", "y":"e", "e":[201, "A Generic Error Occurred"]}
        """
        try:
            transaction_id = self.last_transaction_id.to_bytes(length=2, byteorder='big')
        except OverflowError:
            self.last_transaction_id = 0
            transaction_id = self.last_transaction_id.to_bytes(length=2, byteorder='big')

        self.last_transaction_id += 1
        request = {
            b't': transaction_id,
            b'y': b'q',
            b'q': method,
            b'a': args
        }

        self.transport.sendto(addr=addr, data=b.encode(request))

        future = asyncio.get_event_loop().create_future()
        self.transactions[transaction_id] = future
        try:
            return await future
        except asyncio.CancelledError:
            pass
        finally:
            self.transactions.pop(transaction_id)

    def handle_query(self, decoded, address):
        try:
            method = decoded[b'q'].decode()
        except KeyError:
            return
        try:
            method = getattr(self, "krpc_handle_%s" % method)
        except AttributeError:
            log.debug("Got query with unknown method %s" % method)
            return

        response = method(decoded, address)
        if response is not None:
            self.transport.sendto(addr=address, data=response)

    def datagram_received(self, datagram, address):
        try:
            decoded = b.decode(datagram)
        except b.InvalidBencode:
            log.debug("Discarded invalid datagram (failed to decode)")
            return
        try:
            message_type = decoded[b'y']
            # noinspection PyUnusedLocal
            tid = decoded[b't']
        except KeyError:
            log.debug("Discarded invalid datagram: %s" % decoded)
            return

        if message_type == b'r' or message_type == b'e':
            self.handle_response(decoded)
        elif message_type == b'q':
            self.handle_query(decoded, address)

    def handle_response(self, response):
        transaction_id = response[b't']
        try:
            self.transactions[transaction_id].set_result(response)
        except (KeyError, asyncio.InvalidStateError):
            log.debug("Got response to non-existing or canceled transaction: %s" % response)

    def __init__(self):
        self.transactions = {}
        self.last_transaction_id = 0

    def connection_made(self, transport: asyncio.DatagramTransport):
        # noinspection PyAttributeOutsideInit
        self.transport = transport
