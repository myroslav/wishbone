.. _modules:
=======
Modules
=======

Modules are isolated pieces of code which do not directly invoke each others
functionality.  They merely act upon the messages coming in to its queues and
submit messages into another queue for the next module to process.
Modules run as greenthreads.

Wishbone comes with a set of builtin modules.  Besides these, there's a
collection of :ref:`external modules <external modules>` available which are
developed and released seperately from Wishbone itself.

Wishbone has following module types:

.. toctree::
    input
    output
    flow
    process


A module has an arbirary number of parameters but always needs to accept
:py:class:`wishbone.actorconfig.ActorConfig` which passes Wishbone specific
the characteristics to it:

.. autoclass:: wishbone.actorconfig.ActorConfig
    :members:

