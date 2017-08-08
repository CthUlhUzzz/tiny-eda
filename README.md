**Library provide interface for Event driven programming on top of given message broker.
With it, you can implement interaction between any components of your system.**

Library works with the following abstractions:
* **Message brokers** - Broker for the transfer of events (You can also create your own brokers, by inheriting them from the `AbstractMessageBroker` class).
* **Event router** - The main engine of the library responsible for routing `events` between `event generators`, `event handlers` and `message brokers`.
* **Event generator** - Generator of `events` (Must be an asynchronous generator)
* **Event handler** - The `event` handler with the specified types (Must be an asynchronous function)
* **Event** - Event with `type` and `data` fields.

**Note:** Due to the requirement for asynchronous generators, it only works with *Python 3.6* and above.