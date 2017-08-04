from logging import getLogger

from aioredis import create_connection
from aioredis.pubsub import Receiver
from tiny_eda.broker import AbstractMessageBroker

from . import MessageBrokerConnectionClosed, MessageBrokerNothingToRead


# FIXME: Create reconnection
# TODO: Reuse connections for separated Brokers

class RedisMessageBroker(AbstractMessageBroker):
    def __init__(self, host, port, password=None):
        self.host = host
        self.port = port
        self.password = None or password
        self._logger = getLogger(type(self).__name__)
        # Redis supports only subscribe or publish connection in one time
        self._redis_subscribe_connection = None
        self._redis_publish_connection = None
        self._redis_message_receiver = None

    async def start(self):
        assert self._redis_publish_connection is None and self._redis_subscribe_connection is None and self._redis_message_receiver is None
        self._redis_publish_connection = await create_connection((self.host, self.port), password=self.password)
        self._redis_subscribe_connection = await create_connection((self.host, self.port), password=self.password)
        self._redis_message_receiver = Receiver()
        self._logger.debug('Started')

    async def stop(self):
        assert self._redis_publish_connection is not None and \
               self._redis_subscribe_connection is not None and \
               self._redis_message_receiver is not None

        if not self._redis_publish_connection.closed:
            if self._redis_message_receiver.is_active:
                channels = self._redis_message_receiver.channels.keys()
                await self.unsubscribe(set(channel.decode() for channel in channels))
            self._redis_message_receiver.stop()
            self._redis_message_receiver = None
            self._redis_publish_connection.close()
            await self._redis_publish_connection.wait_closed()
            self._redis_publish_connection = None

        if not self._redis_subscribe_connection.closed:
            self._redis_subscribe_connection.close()
            await self._redis_subscribe_connection.wait_closed()
            self._redis_subscribe_connection = None
            self._logger.debug('Stopped')

    async def publish(self, channel: str, message: str):
        if not self._redis_publish_connection.closed:
            await self._redis_publish_connection.execute('PUBLISH', channel, message)
            self._logger.debug('Message "%s" published on channel "%s"' % (message, channel))
        else:
            raise MessageBrokerConnectionClosed

    async def subscribe(self, channels: set):
        assert len(channels) > 0
        if not self._redis_subscribe_connection.closed:
            subscribed_channels = set(ch.decode() for ch in self._redis_message_receiver.channels)
            in_subscribed_channels = subscribed_channels & channels
            if len(in_subscribed_channels) > 0:
                self._logger.warning('Channels "%s" already subscribed' % '","'.join(in_subscribed_channels))
            channels_for_subscribing = channels - in_subscribed_channels
            wrapped_channels = set(self._redis_message_receiver.channel(ch) for ch in channels_for_subscribing)
            if len(wrapped_channels) > 0:
                await self._redis_subscribe_connection.execute_pubsub('SUBSCRIBE', *wrapped_channels)
                self._logger.debug('Channels "%s" subscribed' % '","'.join(channels_for_subscribing))
        else:
            raise MessageBrokerConnectionClosed

    async def unsubscribe(self, channels: set):
        if not self._redis_subscribe_connection.closed:
            subscribed_channels = set(ch.decode() for ch in self._redis_message_receiver.channels)
            not_in_subscribed_channels = channels - subscribed_channels
            if len(not_in_subscribed_channels) > 0:
                self._logger.warning('Channels "%s" are not yet subscribed' % '","'.join(not_in_subscribed_channels))
            channels_for_unsubscribing = channels - not_in_subscribed_channels
            wrapped_channels = set(self._redis_message_receiver.channel(ch) for ch in channels_for_unsubscribing)
            if len(wrapped_channels) > 0:
                await self._redis_subscribe_connection.execute_pubsub('UNSUBSCRIBE', *wrapped_channels)
                self._logger.debug('Channels "%s" unsubscribed' % '","'.join(channels_for_unsubscribing))
        else:
            raise MessageBrokerConnectionClosed

    async def receive(self) -> tuple:
        if not self._redis_subscribe_connection.closed:
            if self._redis_message_receiver.is_active:
                result = await self._redis_message_receiver.get()
                if result is not None:
                    channel, message = result
                    message = message.decode()
                    channel = channel.name.decode()
                    self._logger.debug('Message "%s" received from channel "%s"' % (message, channel))
                    return channel, message
            raise MessageBrokerNothingToRead
        else:
            raise MessageBrokerConnectionClosed
