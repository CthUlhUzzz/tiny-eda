import asyncio
import logging

from tiny_eda.broker import RedisMessageBroker
from tiny_eda.event import Event
from tiny_eda.router import EventRouter


async def ping_generator():
    yield Event('ping', ['ping'])


async def ping_handler(event):
    return Event('pong', ['pong'])


async def main():
    async with EventRouter(RedisMessageBroker('127.0.0.1', 6379)) as router:
        await router.enable_handler('ping', ping_handler)
        router.enable_generator(ping_generator())
        await router.stopped.wait()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
