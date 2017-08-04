import asyncio
import inspect
import json
import logging

from tiny_eda.event import Event


class EventRouter:
    def __init__(self, message_broker, channel_prefix='event_'):
        self.message_broker = message_broker
        self._generators_results = None
        self.stopped = asyncio.Event()
        self.stopped.set()
        self._working_generators = {}
        self._working_handlers = set()
        self._enabled_handlers = {}
        self._logger = logging.getLogger(type(self).__name__)
        self._process_generators_task = None
        self._process_incoming_events_task = None
        self.channel_prefix = channel_prefix

    def _disable_done_generator(self, future):
        self.disable_generator(future.result())

    def enable_generator(self, generator):
        if not self.stopped.is_set():
            assert inspect.isasyncgen(generator)
            if generator not in self._working_generators:
                future = asyncio.ensure_future(self._wait_generator(generator))
                future.add_done_callback(self._disable_done_generator)
                self._working_generators[generator] = future
                self._logger.debug('Generator "%s" enabled' % generator)
            else:
                self._logger.warning('Generator "%s" already enabled' % generator)

    async def _wait_generator(self, generator):
        if not self.stopped.is_set():
            async for event in generator:
                self._generators_results.put_nowait(event)
            return generator

    def disable_generator(self, generator):
        assert inspect.isasyncgen(generator)
        if not self.stopped.is_set():
            if generator in self._working_generators:
                self._working_generators[generator].cancel()
                del self._working_generators[generator]
                self._logger.debug('Generator "%s" disabled' % generator)
            else:
                self._logger.warning('Generator "%s" is not yet enabled' % generator)

    async def _process_generators(self):
        while True:
            event = await self._generators_results.get()
            assert issubclass(type(event), Event)
            await self._write_event(event)

    async def start(self):
        if self.stopped.is_set():
            assert self._process_generators_task is None and self._process_incoming_events_task is None
            await self.message_broker.start()
            self._generators_results = asyncio.Queue()
            self._process_generators_task = asyncio.ensure_future(self._process_generators())
            self._process_incoming_events_task = asyncio.ensure_future(self._process_incoming_events())
            self.stopped.clear()
            self._logger.debug('Started')

    async def stop(self):
        if not self.stopped.is_set():
            for generator in tuple(self._working_generators.keys()):
                self.disable_generator(generator)
            tasks = []
            for event_type in tuple(self._enabled_handlers):
                for handler in tuple(self._enabled_handlers[event_type]):
                    tasks.append(self.disable_handler(event_type, handler))
            if len(tasks)>0:
                await asyncio.wait(tasks)
            self.stopped = True
            self._process_generators_task.cancel()
            self._process_incoming_events_task.cancel()
            self._process_generators_task = None
            self._process_incoming_events_task = None
            await self.message_broker.stop()
            self._generators_results = asyncio.Queue()
            self._logger.debug('Stopped')

    async def _process_incoming_events(self):
        while True:
            event = await self._read_event()
            if event.type in self._enabled_handlers:
                handlers = {handler(event) for handler in self._enabled_handlers[event.type]}
                assert all(map(lambda x: inspect.isawaitable(x), handlers))
                self._working_handlers.add(asyncio.ensure_future(self._wait_handlers(handlers)))

    async def _wait_handlers(self, handlers):
        for result in asyncio.as_completed(handlers):
            self._generators_results.put_nowait(await result)

    async def _read_event(self):
        channel, data = await self.message_broker.receive()
        if channel.startswith(self.channel_prefix):
            event = Event(channel[len(self.channel_prefix):], json.loads(data))
            self._logger.debug('Event "%s" received from broker' % event)
            return event

    async def _write_event(self, event):
        await self.message_broker.publish(self.channel_prefix + event.type, json.dumps(event.data))
        self._logger.debug('Event "%s" send to broker' % event)

    async def enable_handler(self, event_type, handler):
        assert inspect.isfunction(handler) or inspect.ismethod(handler)
        if not self.stopped.is_set():
            if event_type not in self._enabled_handlers:
                self._enabled_handlers[event_type] = {handler}
                await self.message_broker.subscribe({self.channel_prefix + event_type, })
                self._logger.debug('Handler "%s" enabled on event "%s"' % (handler, event_type))
                return
            else:
                if handler not in self._enabled_handlers[event_type]:
                    self._enabled_handlers[event_type].add(handler)
                    self._logger.debug('Handler "%s" enabled on event "%s"' % (handler, event_type))
                    return
            self._logger.warning('Handler "%s" already enabled on event "%s"' % (handler, event_type))

    async def disable_handler(self, event_type, handler):
        assert inspect.isfunction(handler) or inspect.ismethod(handler)
        if not self.stopped.is_set():
            if event_type in self._enabled_handlers:
                if handler in self._enabled_handlers[event_type]:
                    if len(self._enabled_handlers[event_type]) == 1:
                        del self._enabled_handlers[event_type]
                        await self.message_broker.unsubscribe({self.channel_prefix + event_type, })
                    else:
                        self._enabled_handlers[event_type].remove(handler)
                    self._logger.debug('Handler "%s" disabled on event "%s"' % (handler, event_type))
                    return
            self._logger.warning('Handler "%s" not yet enabled on event "%s"' % (handler, event_type))

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
