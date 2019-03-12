OversimplifiedDHT: A somewhat deficient python implementation of the Bittorrent Mainline DHT.
=============================================================================================

Not suitable for real use. The focus of the project is research.

What works:
-----------
- It bootstraps
- It can find peers
- It responds to pings 💪

Planned features:
-----------------
- `DHT Security extension <http://www.bittorrent.org/beps/bep_0042.html>`_ (in progress)
- Saving the routing table between program invocations
- General compliance with `BEP5 <http://www.bittorrent.org/beps/bep_0005.html>`_



Usage:

.. code-block:: python

    import asyncio

    from oversimplified_dht import Router

    loop = asyncio.get_event_loop()


    async def main():
        r = await Router.create()
        await r.bootstrap()
        print(await r.get_peers(b'\x8b\xde\xb5Pcm;R;-+;\xd4\x9d{\x0f\xc71\x17l'))



    asyncio.get_event_loop().run_until_complete(main())


