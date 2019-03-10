import asyncio
import hashlib

from oversimplified_dht import Router, NodeId

loop = asyncio.get_event_loop()


async def main():
    r = await Router.create(NodeId.from_bytes(hashlib.sha1(b'some random string').digest()))
    await r.bootstrap()
    await asyncio.sleep(4)
    info_hash = b'\x8b\xde\xb5Pcm;R;-+;\xd4\x9d{\x0f\xc71\x17l'
    async for peer_info in r.get_peers(info_hash):
        print(peer_info)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
