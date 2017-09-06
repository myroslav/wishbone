#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  count.py
#
#  Copyright 2017 Jelle Smet <development@smetj.net>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from wishbone.module import FlowModule
from gevent.pool import Pool
from gevent import sleep


class Count(FlowModule):

    '''**Lets events pass through based on the number of times a value occurs.**

    Events pass through after a certain value has occured a predefined number
    of times.

    This counter can also reset and expire after a predefined time.

    An example use case is that an event should occur a number of times within
    a certian timeframe prior to further action is needed.

    A condition has following format:

        { "data": {
            "value": "abc",
            "frequency": 10,
            "window": 60
        }}

    This means if an event of which the <data> field has value "abc" occurs 10
    times within a time window of 60 seconds since the first occurance
    happened, the 10th event will pass through. The first 9 events will get
    dropped.

    Parameters:

        - conditions(dict)({})
           |  The conditions which should be met.

        - expire(int)(0)
           |  The time window in which all occurances should happen.
           |  A value of 0 disables the expiration.


    Queues:

        - inbox
           |  Incoming events

        - outbox
           |  Outgoing events

        - dropped
           |  Events not meeting the counter requirements.

    '''

    def __init__(self, actor_config, conditions={}):
        FlowModule.__init__(self, actor_config)

        self.pool.createQueue("inbox")
        self.pool.createQueue("outbox")
        self.pool.createQueue("dropped")
        self.registerConsumer(self.consume, "inbox")

        self.__counter = {}
        self.__count_down_pool = Pool(len(self.kwargs.conditions))

    def consume(self, event):

        for key, condition in self.kwargs.conditions.items():
            try:
                if event.get(key) == condition["value"]:
                    if key in self.__counter:
                        self.__counter[key] += 1
                        if self.__counter[key] >= condition["frequency"]:
                            self.submit(event, "outbox")
                            break
                    else:
                        self.__counter[key] = 1
                        if condition["window"] > 0:
                            self.__count_down_pool.spawn(self.__countDown, condition["window"], key)

                    self.submit(event, "dropped")
                    self.logging.debug("Event with id '%s' and key '%s' dropped" % (event.get('uuid'), key))

            except KeyError:
                self.logging.debug("Event with id '%s' has no key '%s'." % (
                    event.get('uuid'), key))

    def __countDown(self, seconds, key):

        sleep(seconds)
        del(self.__counter[key])
        self.logging.debug("Time window of '%s' expired for key '%s'." % (seconds, key))
