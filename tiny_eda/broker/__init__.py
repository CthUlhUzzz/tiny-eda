from .redis import RedisMessageBroker
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


__all__ = ['RedisMessageBroker', 'AbstractMessageBroker']
