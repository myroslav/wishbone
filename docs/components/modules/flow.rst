.. _flow:
====
Flow
====


.. note::

    Flow modules conditionally alter the flow of events between modules.

Flow modules select the outgoing queue to which incoming events are submitted
based on certain conditions.  For example, Wishbone queues can only be
connected 1 queue.

If you need a `1-to-many` or a `many-to-1` queue connection then you can use
the :py:class:`wishbone.module.fanout.Fanout` or
:py:class:`wishbone.module.funnel.Funnel` respectively.

Some of the characteristics of `output` modules are:

* They do not alter the content of events flowing through except optionally
  setting some contextual data.

----

``Flow`` module bases :py:class:`wishbone.module.FlowModule`:

.. autoclass:: wishbone.module.FlowModule
    :members:
    :show-inheritance:
    :inherited-members:




