#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test_functions_template.py
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

from wishbone.componentmanager import ComponentManager
import time
import os
import re


def test_wishbone_function_template_choice():

    lst = ["one", "two", "three"]
    f = ComponentManager().getComponentByName("wishbone.function.template.choice")(lst)
    assert f.lookup() in lst


def test_wishbone_function_template_cycle():

    lst = ["one", "two", "three"]
    f = ComponentManager().getComponentByName("wishbone.function.template.cycle")(lst)
    assert f.lookup() == "one"
    assert f.lookup() == "two"
    assert f.lookup() == "three"
    assert f.lookup() == "one"


def test_wishbone_function_template_epoch():

    f = ComponentManager().getComponentByName("wishbone.function.template.epoch")()
    assert type(f.lookup()) == float
    epoch = f.lookup()
    assert epoch > 0 and epoch < time.time()


def test_wishbone_function_template_pid():

    f = ComponentManager().getComponentByName("wishbone.function.template.pid")()
    assert f.lookup() == os.getpid()


def test_wishbone_function_template_random_bool():

    f = ComponentManager().getComponentByName("wishbone.function.template.random_bool")()
    assert f.lookup() in [True, False]


def test_wishbone_function_template_random_integer():

    f = ComponentManager().getComponentByName("wishbone.function.template.random_integer")(10, 15)
    value = f.lookup()
    assert value >= 10 and value <= 15


def test_wishbone_function_template_random_uuid():

    f = ComponentManager().getComponentByName("wishbone.function.template.random_uuid")()
    value = f.lookup()
    assert re.compile('[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}', re.I).match(value) is not None


def test_wishbone_function_template_random_word():

    f = ComponentManager().getComponentByName("wishbone.function.template.random_word")()
    value = f.lookup()
    assert re.compile('\w*').match(value) is not None


def test_wishbone_function_template_strftime():

    f = ComponentManager().getComponentByName("wishbone.function.template.strftime")()
    assert f.lookup(0, 'YYYY-MM-DD HH:mm:ss ZZ') == '1970-01-01 00:00:00 +00:00'
