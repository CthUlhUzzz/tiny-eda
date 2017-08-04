Example:
```python
import asyncio
import logging

from broker.redis import RedisMessageBroker
from event import Event
from router import EventRouter


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
```