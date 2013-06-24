#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  stdout.py
#
#  Copyright 2013 Jelle Smet <development@smetj.net>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
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
from time import time
from gevent import socket
from sys import argv


class Graphite(Actor):

    '''*A builtin Wishbone module which formats the internal metric format into a
    Graphite compatible format.*

    The module finds out the script name it runs from, strips of the .py part
    and uses that as part of the metric name.  For example:

    - wishbone_test.function.tcpout.consume.hits
    - wishbone_test.queue.buffer.inbox.in_rate



    Parameters:

        name(str):  The name of the module.

    '''

    def __init__(self, name):
        Actor.__init__(self, name)
        self.name=name
        self.script_name = argv[0].replace(".py","")
        self.logging.info("Initiated")

    def consume(self, event):
        for item in [ "queue","function" ]:
            for one in event["data"][item]:
                for two in event["data"][item][one]:
                    try:
                        self.queuepool.outbox.put({"header":{}, "data":"wishbone.%s.%s.%s.%s %s %s\n"%(self.script_name, item, one, two, event["data"][item][one][two], time())})
                    except:
                        pass