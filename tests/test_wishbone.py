#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test_wishbone.py
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

import pytest
from gevent import spawn
from wishbone import QueuePool
from wishbone import Queue

from wishbone.module import Fanout
from wishbone.event import Event

from wishbone.router import Default
from wishbone.module import TestEvent
from wishbone.module import Fanout

from gevent import sleep

def test_listQueues():
    q = QueuePool(1)
    q.createQueue("hello")
    assert list(q.listQueues(names=True)) == ['hello', 'admin_out', 'admin_in', 'failed', 'success', 'logs', 'metrics']


def test_createQueue():
    q = QueuePool(1)
    q.createQueue("test")
    assert (q.queue.test)


def test_hasQueue():
    q = QueuePool(1)
    q.createQueue("test")
    assert (q.hasQueue("test"))


def test_getQueue():
    q = QueuePool(1)
    q.createQueue("test")
    assert isinstance(q.getQueue("test"), Queue)


def test_wishbone_flow_fanout():

    router = Default()
    router.registerModule(TestEvent, "input", interval=1)
    router.registerModule(Fanout, "fanout")
    router.connect("input.outbox", "fanout.inbox")
    router.pool.getModule("fanout").pool.createQueue("one")
    router.pool.getModule("fanout").pool.createQueue("two")
    router.start()
    sleep
    router.pool.getModule("fanout").pool.getQueue("one").get()
