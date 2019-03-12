import asyncio

from oversimplified_dht import Router

loop = asyncio.get_event_loop()


async def main():
    r = await Router.create()
    await r.bootstrap()
    print(await r.get_peers(b'\x8b\xde\xb5Pcm;R;-+;\xd4\x9d{\x0f\xc71\x17l'))


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
