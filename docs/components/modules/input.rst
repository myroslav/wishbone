.. _input:
=====
Input
=====

.. note::

    Input modules either take events from the outside world or generate events.


Some of the characteristics of `input` modules are:

* They have a :ref:`protocol decoder method <decode>` mapped to
  :func:`wishbone.module.InputModule.decode` in order to convert the incoming
  data into a workable datastructure.

* :paramref:`wishbone.actorconfig.ActorConfig.protocol_function` determines
  whether :func:`wishbone.module.InputModule.generateEvent` either expects
  events from the outside world to be Wishbone events or regular data.

* Contextual data about the incoming event can/should be stored under
  ``tmp.<module name>``.

-----

``Input`` module bases :py:class:`wishbone.module.InputModule`:

.. autoclass:: wishbone.module.InputModule
    :members:
    :show-inheritance:
    :inherited-members:
