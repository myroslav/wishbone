.. _output:
======
Output
======


.. note::

    Output modules submit data to external services.


Some of the characteristics of `output` modules are:

* They have a :ref:`protocol encoder method <encode>` mapped to
  :func:`wishbone.module.OutputModule.encode` in order to convert the desired
  :py:class:`wishbone.event.Event` payload into the desired format prior to
  submitting it to the external service.

* They should **always** provide a ``selection`` and ``payload`` module parameter.
  If ``payload`` is not ``None``, then it takes precendence over ``selection``. ``Selection``
  defines the event key to submit whilst template comes up with
  a string to submit.  ``payload`` usually makes no sense with bulk events.


----

``Output`` modules inherit the :py:class:`wishbone.module.OutputModule` baseclass:

.. autoclass:: wishbone.module.OutputModule
    :members:
    :show-inheritance:
    :inherited-members:




