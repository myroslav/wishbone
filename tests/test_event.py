#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test_wishbone.py
#
#  Copyright 2016 Jelle Smet <development@smetj.net>
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

from wishbone.event import Event


def test_event_bulk_default():

    e = Event(bulk=True)
    assert e.dump()["bulk"]


def test_event_appendBulk():

    e = Event(bulk=True)
    ee = Event({"one": 1})

    e.appendBulk(ee)
    assert e.dump()["data"][0]["uuid"] == ee.data["uuid"]


def test_event_appendBulkBad():

    normal_event = Event()

    try:
        normal_event.appendBulk(Event())
    except Exception:
        assert True
    else:
        assert False

    bulk_event = Event(bulk=True)
    try:
        bulk_event.appendBulk("hello")
    except Exception:
        assert True
    else:
        assert False


def test_event_clone():

    a = Event({"one": 1, "two": 2})
    b = a.clone()

    assert id(a.data) != id(b.data)
    assert not a.data["cloned"]
    assert b.data["cloned"]
    assert b.data["uuid_previous"][0] == a.data["uuid"]


def test_event_format():

    e = Event({"one": 1, "two": 2})
    assert e.render("{{one}} is a number and so is {{two}}") == "1 is a number and so is 2"


def test_event_uuid():

    e = Event()
    assert e.get('uuid')
