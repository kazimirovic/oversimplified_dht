OversimplifiedDHT: A somewhat deficient python implementation of the Bittorrent Mainline DHT.
=============================================================================================

Not suitable for real use. The main focus of the project is research.

What works:
-----------
- It bootstraps
- It can find peers
- It responds to pings 💪

Planned features:
-----------------
- Save the routing table between program invocations
- General compliance with `BEP5 <http://www.bittorrent.org/beps/bep_0005.html>`_
- (Eventually) `DHT Security extension <http://www.bittorrent.org/beps/bep_0042.html>`_

The current version doesn't use buckets as described in `BEP5 <http://www.bittorrent.org/beps/bep_0005.html>`_, and therefore is very inefficient. 

Usage:

.. code-block:: python

    import asyncio
    import hashlib

    from oversimplified_dht import Router, NodeId

    loop = asyncio.get_event_loop()


    async def main():
        r = await Router.create(NodeId.from_bytes(hashlib.sha1(b'some random string').digest()))
        await r.bootstrap()
        info_hash = b'\x8b\xde\xb5Pcm;R;-+;\xd4\x9d{\x0f\xc71\x17l' # a real torrent file's info hash
        async for peer_info in r.get_peers(info_hash):
            print(peer_info)


    if __name__ == '__main__':
        asyncio.get_event_loop().run_until_complete(main())




