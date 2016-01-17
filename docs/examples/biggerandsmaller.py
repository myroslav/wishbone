#!/usr/bin/env python

from wishbone import Actor


class BiggerAndSmaller(Actor):

    '''**Checks whether an integer is between min and max.**

    Checks whether an integer is between the defined minimum and maximum
    values.  When the value is inside the scope it is submitted to the
    *inside* queue otherwise it is submitted to the *outside* queue.


    Parameters:

        - selection(str)('@data')
           |  The value

        - min(int)(1)
           |  The minimum integer value.

        - max(int)(100)
           |  The maximum integer value.

    Queues:

        - inbox
           |  Incoming messages

        - inside
           |  Values are inside the <min> and <max> values.

        - outside
           |  Values are outside the <min> and <max> values.
    '''

    def __init__(self, actor_config, selection='@data', min=1, max=100):
        Actor.__init__(self, actor_config)

        self.pool.createQueue("inbox")
        self.pool.createQueue("inside")
        self.pool.createQueue("outside")
        self.registerConsumer(self.consume, "inbox")

    def consume(self, event):

        if not isinstance(event.data, int):
            raise TypeError("Event data is not type integer")

        if event.get(self.kwargs.selection) >= self.kwargs.min and event.data <= self.kwargs.max:
            self.submit(event, self.pool.queue.inside)
        else:
            self.submit(event, self.pool.queue.outside)

