=============
Event Modules
=============

    *Event modules are building blocks which perform 1 clearly defined action
    to the events passing through them.*


Event modules are functionally isolated blocks of code which do not directly
invoke each other's functionality.  They only interact by passing
:py:class:`wishbone.event.Event` instances to each other's
:py:class:`wishbone.Queue` queues from where the incoming events are consumed
and processed by a function registered by
:py:func:`wishbone.actor.Actor.registerConsumer`.

*Event modules* run as `Gevent greenlets`_ in the background and are created
by inheriting :py:class:`wishbone.actor.Actor` as a baseclass and live inside a
:py:class:`wishbone.router.Default` instance.

Modules typically have, but are not limited to an **inbox**, **outbox**,
**success** and **failed** queue.

A queue can only be connected to 1 single queue.

.. note::

  If you need to have *"one to many"* or *"many to one"* connections then you
  can use the  :py:class:`wishbone.module.Fanout` and
  :py:class:`wishbone.module.Fanout` modules.

The :py:class:`wishbone.actor.Actor` baseclass must be initialized by passing a
:py:class:`wishbone.actor.Actor.ActorConfig` instance which controls the behavior of
the module instance.

.. autoclass:: wishbone.actor.Actor
    :members:
    :show-inheritance:
    :inherited-members:


.. warning::

    When a queue is not connected any message submitted to it will be dropped.
    This is by design to ensure queues do not fill up without ever being
    consumed.

.. toctree::
    module_types/index
    builtin_modules/index
    external_modules/index


Logs
----

Each event module has a :py:class:`wishbone.Logging` instance called
``self.logging`` which can be used to generate logs.  The user is responsible
for connecting the necessary modules to collect and process the log events
from each of the modules' ``logs`` queue.

.. code-block:: python

# TODO(smetj): write about new style


.. note::

  If you are `bootstrapping`_ a server from CLI then the ``logs`` queue of
  each module will be connected to ``stdout`` or ``syslog`` depending on the
  startup mode.

.. warning::

  If no module is consuming the logs from the module's ``logs`` queue, adding
  new logs events to the full queue will cause the event to be dropped.


Metrics
-------

Each Wishbone module collects statistics of its queues.  These metric events
are submitted to the modules' ``metrics`` queue.  The user is responsible for
connecting the necessary modules to collect and process the metric events from
each of the modules' ``metrics`` queue.

Metrics are generated at the interval determined by the
:py:class:`wishbone.actor.Actor.ActorConfig` instance passed to the module.

# TODO(smetj): Write about new style





.. _greenlets: https://greenlet.readthedocs.org/en/latest/
.. _Gevent greenlets: http://www.gevent.org/gevent.html#greenlet-objects
.. _bootstrapping: ../bootstrap/index.html
