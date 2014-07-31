#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  msgpackencode.py
#
#  Copyright 2014 Jelle Smet <development@smetj.net>
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

from wishbone import Actor
from wishbone.error import QueueFull
import msgpack


class MSGPackEncode(Actor):
    '''
    **Encodes events to MSGPack format.**

    Encodes the payload or complete events to MSGPack format.

    Parameters:

        - name(str)
           |  The name of the module.

        - size(int)
           |  The default max length of each queue.

        - frequency(int)
           |  The frequency in seconds to generate metrics.

        - complete(bool)(False)
           |  When True encodes the complete event.  If False only
           |  encodes the data part.

    Queues:

        - inbox
           |  Incoming messages

        - outbox
           |  Outgoing messges
    '''

    def __init__(self, name, size, frequency, complete=False):
        Actor.__init__(self, name, size, frequency)

        self.complete = complete
        self.pool.createQueue("inbox")
        self.pool.createQueue("outbox")

        if self.complete:
            self.encode = self.__encodeComplete
        else:
            self.encode = self.__encodeData

        self.registerConsumer(self.consume, "inbox")

    def consume(self, event):
        event = self.encode(event)
        self.pool.queue.outbox.put(event)

    def __encodeComplete(self, event):
        event["data"] = msgpack.packb(event)
        return event

    def __encodeData(self, event):
        event["data"] = msgpack.packb(event["data"])
        return event



