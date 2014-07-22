===============
Builtin Modules
===============

Wishbone comes with a set of builtin modules.  Modules are isolated blocks of
functionality which are connected to each other within a router instance.

There are different types of modules:

    - input modules
    - output modules
    - flow modules
    - function modules

Besides the builtin modules there is also a list modules which are developed
and maintained apart from Wishbone.  They include tcp/udp servers and clients,
amqp client, etc ...

https://github.com/smetj/wishboneModules


Input modules
-------------

Input modules take input from the outside world into the Wishbone framework.
They often have only 1 :class:`wishbone.tools.WishboneQueue` called **outbox**
in which incoming events go. Input modules are also responsible to format any
incoming data into the expected Wishbone internal event format.

--------

wishbone.input.disk
*******************
.. autoclass:: wishbone.module.DiskIn

--------

wishbone.input.testevent
************************
.. autoclass:: wishbone.module.TestEvent

--------

wishbone.input.tcp
******************
.. autoclass:: wishbone.module.TCPIn

--------

wishbone.input.amqp
*******************
.. autoclass:: wishbone.module.AMQPIn


Output modules
--------------

Output modules take input from another module registered in the Wishbone
router and submit these events to the outside world. They often have only 1
:class:`wishbone.tools.WishboneQueue` called **inbox** in which events arrive
destined to go out. They typically act as TCP, AMQP or other network protocol
clients.

Output modules often have a rescue queue to which events which failed to go
out.

--------

wishbone.output.disk
********************
.. autoclass:: wishbone.module.DiskOut

--------

wishbone.output.amqp
********************
.. autoclass:: wishbone.module.AMQPOut

--------

wishbone.output.stdout
**********************
.. autoclass:: wishbone.module.STDOUT

--------

wishbone.output.tcp
*******************
.. autoclass:: wishbone.module.TCPOut

--------

wishbone.output.syslog
**********************
.. autoclass:: wishbone.module.Syslog

--------

wishbone.output.null
********************
.. autoclass:: wishbone.module.Null

--------


Flow modules
------------

Flow modules allow a user to organize the flow of events.


--------

wishbone.flow.funnel
********************
.. autoclass:: wishbone.module.Funnel

--------

wishbone.flow.fanout
********************
.. autoclass:: wishbone.module.Fanout

--------

wishbone.flow.roundrobin
************************
.. autoclass:: wishbone.module.RoundRobin

--------

Flow modules accept and forward events from and to other modules.  They
fulfill a key roll in building a message flow.  Since you can only have a 1:1
relationship between queues, you cannot split or merge event streams.  That's
where flow modules come handy.  Flow modules are not expected to alter events
when transiting the module.


Function modules
----------------

Function modules accept and forward events from and to other modules.  They
can have a wide range of functionality and change events when transiting the
module.