.. _modules:
=======
Modules
=======

Besides these,
there is a collection of :ref:`external modules <external modules>`  which are
developed and released seperately from Wishbone itself.


output modules should, by convention, provide a <selection> and <payload>
parameter. If payload is not None, then it takes precendence over selection.
Selection defines the key content of the event to submit whilst template comes
up with a string to submit.  <payload> usually makes no sense with bulk events


.. toctree::
    input
    output
    flow
    process
