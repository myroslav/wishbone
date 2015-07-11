#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  graphite.py
#
#  Copyright 2015 Jelle Smet <development@smetj.net>
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
from wishbone.event import Metric
from os.path import basename
from sys import argv
from os import getpid


class Graphite(Actor):

    '''**Converts the internal metric format to Graphite format.**

    Incoming metrics have following format:

        (time, type, source, name, value, unit, (tag1, tag2))
        (1381002603.726132, 'wishbone', 'hostname', 'queue.outbox.in_rate', 0, '', ())



    Parameters:

        - prefix(str)
           |  Some prefix to put in front of the metric name.

        - script(bool)(True)
           |  Include the script name.

        - pid(bool)(False)
           |  Include pid value in script name.

        - source(bool)(True):
           |  Include the source name in the naming schema.


    Queues:

        - inbox
           |  Incoming messages

        - outbox
           |  Outgoing messges
    '''

    def __init__(self, actor_config, prefix='', script=True, pid=False, source=True):
        Actor.__init__(self, actor_config)

        self.pool.createQueue("inbox")
        self.pool.createQueue("outbox")
        self.registerConsumer(self.consume, "inbox")

    def preHook(self):

        if self.kwargs.script:
            self.script_name = '.%s' % (basename(argv[0]).replace(".py", ""))
        else:
            self.script_name = ''

        if self.kwargs.pid:
            self.pid = "-%s" % (getpid())
        else:
            self.pid = ''

        if self.kwargs.source:
            self.doConsume = self.__consumeSource
        else:
            self.doConsume = self.__consumeNoSource

    def consume(self, event):

        if isinstance(event.data, Metric):
            pass
        else:
            self.logging.error("Metric dropped because not of type <wishbone.event.Metric>")

        self.doConsume(event)

    def __consumeSource(self, event):

        event.data = "%s%s%s%s.%s.%s.%s %s %s" % (self.kwargs.prefix, event.data.source, self.script_name, self.pid, event.data.module, event.data.queue, event.data.name, event.data.value, event.data.time)
        self.submit(event, self.pool.queue.outbox)

    def __consumeNoSource(self, event):

        event.data = "%s%s%s.%s.%s.%s %s %s" % (self.kwargs.prefix, self.script_name, self.pid, event.data.module, event.data.queue, event.data.name, event.data.value, event.data.time)
        self.submit(event, self.pool.queue.outbox)
