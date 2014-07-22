================
Wishbone modules
================

Introduction
------------

Modules are isolated blocks of code (greenlets) each with their own specific
functionality. They are created by having a class inherit
:py:class:`wishbone.Actor` as a baseclass. Modules cannot (and are not
supposed to) directly invoke each others functionality. Their only means of
interaction is by passing events to each other's
:py:class:`wishbone.Queue` queues. Modules typically have, but are not limited
to, an inbox, outbox, successful and failed queue.

A module's queues always live inside a :py:class:`wishbone.QueuePool` which,
besides offering some convenience functions, is nothing more than a container
to centralize all the module's queues. Typically, modules consume the events
entering the *inbox* queue and apply to them to some method.  Registering some
module's method to consume all events of a queue is done using
:py:class:`wishbone.Actor.registerConsumer`.  This registered method is then
responsible to submit the event to another queue of choice, typically but not
necessarily *outbox*.


Module categories
-----------------

Modules are stored into a hierarchical name space.  The name of a module
consists out of the *category name + group name + module name*.

Wishbone comes with a set of builtin modules which are an integral part of the
Wishbone framework.

External modules are regular Python modules which create an entrypoint in the
*wishbone.contrib* namespace.

https://github.com/smetj/wishboneModules is a repository containing additional
modules.


You  can list all available modules using the *list* command:

.. code-block:: sh

    $ wishbone list
    +------------------+----------+----------------+---------+------------------------------------------------------------+
    | Category         | Group    | Module         | Version | Description                                                |
    +------------------+----------+----------------+---------+------------------------------------------------------------+
    |                  |          |                |         |                                                            |
    | wishbone         | flow     | funnel         |   0.5.0 | Funnel multiple incoming queues to 1 outgoing queue.       |
    |                  |          | fanout         |   0.5.0 | Funnel multiple incoming queues to 1 outgoing queue.       |
    |                  |          | roundrobin     |   0.5.0 | Round-robins incoming events to all connected queues.      |
    |                  |          |                |         |                                                            |
    |                  | encode   | humanlogformat |   0.5.0 | Formats Wishbone log events.                               |
    |                  |          | graphite       |   0.5.0 | Converts the internal metric format to Graphite format.    |
    |                  |          |                |         |                                                            |
    |                  | function | header         |   0.5.0 | Adds information to event headers.                         |
    |                  |          |                |         |                                                            |
    |                  | input    | disk           |   0.5.0 | Reads messages from a disk buffer.                         |
    |                  |          | testevent      |   0.5.0 | Generates a test event at the chosen interval.             |
    |                  |          | tcp            |   0.5.0 | A Wishbone input module which listens on a TCP socket.     |
    |                  |          | amqp           |   0.5.0 | Consumes messages from AMQP.                               |
    |                  |          |                |         |                                                            |
    |                  | output   | disk           |   0.5.0 | Writes messages to a disk buffer.                          |
    |                  |          | amqp           |   0.5.0 | Produces messages to AMQP.                                 |
    |                  |          | stdout         |   0.5.0 | Prints incoming events to STDOUT.                          |
    |                  |          | tcp            |   0.5.0 | A Wishbone ouput module which writes data to a TCP socket. |
    |                  |          | syslog         |   0.5.0 | Writes log events to syslog.                               |
    |                  |          | null           |   0.5.0 | Purges incoming events.                                    |
    |                  |          |                |         |                                                            |
    | wishbone.contrib | function | skeleton       |     0.1 | A bare minimum Wishbone function module.                   |
    |                  |          |                |         |                                                            |
    +------------------+----------+----------------+---------+------------------------------------------------------------+


To read the help and module instruction use the **show** command:

.. code-block:: sh

    $ wishbone show --module wishbone.input.testevent
    Module "wishbone.input.testevent" version 0.5.0
    ===============================================

    Generates a test event at the chosen interval.
    ----------------------------------------------



        Events have following format:

            { "header":{}, "data":"test" }

        Parameters:

            -   name(str)
                The name of the module.

            -   size(int)
                The default max length of each queue.

            -   frequency(int)
                The frequency in seconds to generate metrics.

            - interval (float):     The interval in seconds between each generated event.
                                    A value of 0 means as fast as possible.
                                    default: 1

            - message (string):     The content of the test message.
                                    default: "test"

            - numbered (bool):      When true, appends a sequential number to the end.
                                    default: False

        Queues:

            - outbox:    Contains the generated events.



Module groups
-------------

Wishbone modules are divided into 6 group types depending on their
functionality:

input modules
~~~~~~~~~~~~~

Input modules take input from the outside into the Wishbone framework.  They
are responsible of accepting data and converting that data into the
appropriate Wishbone data format.  Input modules typically have a
:py:class:`wishbone.Queue` named *output*.

output modules
~~~~~~~~~~~~~~

Output modules are responsible for submitting Wishbone event data to the
outside world.

flow modules
~~~~~~~~~~~~

Flow modules do not change data but they manipulate the flow of events in the
pipeline.

function modules
~~~~~~~~~~~~~~~~

Function modules change event data.

encode modules
~~~~~~~~~~~~~~

Encode modules are responsible for converting the internal metric or log
events into another format.

decode modules
~~~~~~~~~~~~~~

Decode modules convert external metric or log events into the internal format.


Important properties and behavior
---------------------------------

successful and failed queues
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each module has a *successful* and *failed* queue.  Whenever a registered
method (using :py:class:`wishbone.Actor.registerConsumer`) fails to process an
event, the framework will submit the event into the failed queue.  Therefor it
is important not to trap exceptions in the *registered consumer methods* but
rather rely on another module to process the events from the module's failed
queue in order to achieve an error coping strategy when desired.
An example which takes advantage of this behavior might be connecting the
*failed* queue of the :py:class:`wishbone.module.TCPOut` module to the *inbox*
queue of the :py:class:`wishbone.module.DiskOut` module.

On the other side, each time a *registered consumer method* successfully
processes an event, it will automatically be submitted to the *successful*
queue, from where it can be further processed by another module when desired.
An example which takes advantage of this behavior might be connecting the
*successful* queue of the :py:class:`wishbone.module.TCPOut` module to the
*acknowledgment* queue of the :py:class:`wishbone.module.AMQPOut` module.

It's up to the *registered consumer method* to submit the event to some queue
such as *outbox* from where it can be routed to the next module for further
processing.

metrics and logs queues
~~~~~~~~~~~~~~~~~~~~~~~

Each module also has a *metrics* and *logs* queue which hold metric events and
log events respectively, ready to be consumed by another module.


Queues drop data by default
~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a queue is not connected then all messages submitted to it will be
dropped.  The moment a queue is connected to another queue, messages are
buffered.

A module's default parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :py:class:`wishbone.Actor` baseclass can be initialized with 2 parameters:

- size: determines the size of each queue in the module.
- frequency: determines the frequency at which metrics are generated.

Events
------

Events are very simple *<type 'dict'>* data structures which contain a
*header* and a *data* key.

The *header* is a again a *<type 'dict'>* while, *data* can be any type of
object.

.. code-block:: python

    { "header":{}, "data": object }


Example
-------

Consider following example module which reverses the content of incoming
events and optionally converts the first letter into a capital.

.. literalinclude:: examples/reversedata.py
   :language: python
   :linenos:

--------

- The ReverseData class inherits the :py:class:`wishbone.Actor` base class[4].
- The :py:class:`wishbone.Actor` base class is initialized with name,
  size and frequency parameter [23].
- Two queues, inbox and outbox are created [24][25].
- The *consume* method [36] is registered to consume each event from the
  *inbox* queue using the :py:class:`wishbone.Actor.registerConsumer`
  method[26].
- The *preHook* [30] method is executed before starting the registered
  consumer methods while the the *postHook* [33] method is executed before
  shutdown. They are invoked automatically by the Wishbone framework.
- Logging is done by simply invoking the appropriate
  :py:class:`wishbone.Logging` functions.
- The registered consumer method is responsible for adding the (changed) event
  to the appropriate queue. [46]
