.. image:: pics/ascii.png
.. image:: pics/GitHub-Mark-64px.png
    :align: right
    :target: https://github.com/smetj/wishbone
**A pragmatists framework to build reactive event processing services.**

What?
-----

Wishbone is a **Python** framework to build reactive event processing
services by combining and connecting modules into a :ref:`processing pipeline
<processing pipeline>` through which :ref:`events <events>` flow, modify and
trigger interactions with remote services.

The framework can be used to implement a wide area of solutions such as
`mashup enablers`_, `ETL servers`_, `stream processing servers`_, `webhook
services`_ , `ChatOps services`_, bots and all kinds of event driven
automation.

Why?
----

The goal of the project is to provide an expressive and ops friendly framework
to build pragmatic (micro)services taking as much boilerplate away such as:

* Easily including your custom code
* Process management
* Error handling
* Logging
* Metrics
* Full server setup using YAML config files


How?
----

For an overview of examples visit the :ref:`examples <examples>` page.


.. toctree::
    :hidden:

    installation/index
    components/index
    server/index
    examples/index
    scenarios/index
    python/index


.. _mashup enablers: https://en.wikipedia.org/wiki/Mashup_(web_application_hybrid)#Mashup_enabler
.. _ETL servers: https://en.wikipedia.org/wiki/Extract,_transform,_load
.. _stream processing servers: https://en.wikipedia.org/wiki/Stream_processing
.. _CEP: https://en.wikipedia.org/wiki/Complex_event_processing
.. _ChatOps services: https://www.google.com/search?newwindow=1&q=chatops
.. _webhook services: https://en.wikipedia.org/wiki/Webhook
