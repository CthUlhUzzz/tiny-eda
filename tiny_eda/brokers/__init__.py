from abc import ABCMeta, abstractmethod


class MessageBrokerConnectionClosed(Exception):
    pass


class MessageBrokerNothingToRead(Exception):
    pass


class AbstractMessageBroker(metaclass=ABCMeta):
    @abstractmethod
    async def publish(self, channel, message):
        raise NotImplementedError

    @abstractmethod
    async def subscribe(self, channels):
        raise NotImplementedError

    @abstractmethod
    async def unsubscribe(self, channels):
        raise NotImplementedError

    @abstractmethod
    async def receive(self):
        raise NotImplementedError

    @abstractmethod
    async def start(self):
        raise NotImplementedError

    @abstractmethod
    async def stop(self):
        raise NotImplementedError

from .redis import RedisMessageBroker

brokers_map = {'Redis': RedisMessageBroker}

__all__ = ['RedisMessageBroker', 'AbstractMessageBroker']
