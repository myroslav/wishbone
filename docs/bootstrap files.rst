===============
Bootstrap Files
===============

Bootstrap files are YAML formatted configuration files used to start a
Wishbone server.

Example usage:

.. code::

    $ wishbone start --config static_dynamic.yaml


A bootstrap file consist out of 3 sections:

Sections
--------

lookups
~~~~~~~

**lookups section extract**

.. code-block:: yaml

    lookups:
      randomword:
        module: wishbone.lookup.randomword
      event:
        module: wishbone.lookup.event

The *lookups* section is a *dictionary of dictionaries* defining the lookup
functions which can be used to provide values for the UpLook_ based module
argument values.

The keys are are mapped to the function names used in the arguments in the
module section. For example *line 3* defines a lookup function named
*randomword* which is used on *line 12* and *line 25* as a module argument values.

Each entry requires a *module* entry which defines the module name which
should be imported.  The last part of the dotted name is the actual function
which should get imported.

For example **wishbone.lookup.randomword** is imported as:

.. code::

    from wishbone.lookup import randomword

The *lookups* section is optional if you're not using any UpLook variables


modules
~~~~~~~

**modules section extract**

.. code-block:: yaml

    modules:
      static:
        module: wishbone.input.testevent
        arguments:
          message : ~randomword()
          interval: 1

      dynamic:
        module: wishbone.input.testevent
        arguments:
          message: ~~randomword()
          interval: 1

The *modules* section is a *dictionary of dictionaries* containing the
Wishbone modules to initialize. Each key is the module instance name.  Each
instance is again a dictionary containing 2 values:

- module: The wishbone module to load (see *wishbone list*)
- arguments: A dictionary of keyword arguments used to initialize the module.


routingtable
~~~~~~~~~~~~

**routing table section extract**

.. code-block:: yaml

    routingtable:
      - static.outbox         -> static_header.inbox
      - static_header.outbox  -> funnel.static
      - dynamic.outbox        -> dynamic_header.inbox


The routing table section determines which module queues should be connected
to one another in order to achieve the desired event stream resulting into the
desired outcome.

The section consists out of a list of entries containing a source
queue, a separator -> and a destination queue.

A queue can only be connected to 1 single queue.  If you need to have *"one to
many"* or *"many to one"* constructions then you need to use the
:py:class:`wishbone.module.Fanout` and :py:class:`wishbone.module.Fanout`.


Example file
------------

.. literalinclude:: examples/static_dynamic.yaml
   :language: yaml
   :linenos:




.. _UpLook: https://github.com/smetj/uplook