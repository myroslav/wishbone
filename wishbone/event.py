#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  event.py
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

import arrow
import time
from wishbone.error import BulkFull, InvalidData, InvalidEventFormat, TTLExpired
from uuid import uuid4
from jinja2 import Template
from jinja2 import Undefined
from easydict import EasyDict
from copy import deepcopy


class SilentUndefined(Undefined):
    '''
    Dont break pageloads because vars arent there!
    '''
    def _fail_with_undefined_error(self, *args, **kwargs):
        return None


EVENT_RESERVED = ["timestamp", "version", "data", "tmp", "errors", "uuid", "uuid_previous", "cloned", "bulk"]


class Bulk(object):

    def __init__(self, max_size=None, delimiter="\n"):
        self.__events = []
        self.max_size = max_size
        self.delimiter = delimiter
        self.error = None

    def append(self, event):
        '''
        Appends an event to the bulk object.
        '''

        if isinstance(event, Event):
            if self.max_size is None or len(self.__events) < self.max_size:
                self.__events.append(event)
            else:
                raise BulkFull("Max number of events (%s) is reached." % (self.max_size))
        else:
            raise InvalidData()

    def clone(self):
        '''
        Returns a cloned version of the Bulk event using deepcopy.
        '''

        e = Bulk()
        e.__events = self.deepishCopy(self.__events)
        return e

    def dump(self):
        '''
        Returns an iterator returning all contained events
        '''

        for event in self.__events:
            yield event

    def dumpFieldAsList(self, field="data"):
        '''
        Returns a list containing a specific field of each stored event.
        Events with a missing field are skipped.
        '''

        result = []
        for event in self.dump():
            try:
                result.append(event.get(field))
            except KeyError:
                pass
        return result

    def dumpFieldAsString(self, field="data"):
        '''
        Returns a string joining <field> of each event with <self.delimiter>.
        Events with a missing field are skipped.
        '''

        result = []
        for event in self.dump():
            try:
                result.append(event.get(field))
            except KeyError:
                pass

        return self.delimiter.join(result)

    def size(self):
        '''
        Returns the number of elements stored in the bulk.
        '''

        return len(self.__events)

    def deepishCopy(self, org):
        '''
        much, much faster than deepcopy, for a dict of the simple python types.

        Blatantly ripped off from https://writeonly.wordpress.com/2009/05/07
        /deepcopy-is-a-pig-for-simple-data/
        '''

        if isinstance(org, dict):
            out = dict().fromkeys(org)
            for k, v in list(org.items()):
                try:
                    out[k] = v.copy()   # dicts, sets
                except AttributeError:
                    try:
                        out[k] = v[:]   # lists, tuples, strings, unicode
                    except TypeError:
                        out[k] = v      # ints

            return out
        else:
            return org


class Event(object):

    '''The Wishbone event object.

    A class object containing the event data being passed from one Wishbone
    module to the other.

    Args:

        data (dict/list/string/int/float): The data to assign to the <data> field.
        ttl (int): The TTL value for the event.
    '''

    def __init__(self, data=None, ttl=254, bulk=False):

        self.data = {
            "cloned": False,
            "bulk": bulk,
            "data": None,
            "errors": {
            },
            "tags": [],
            "timestamp": time.time(),
            "tmp": {
            },
            "ttl": ttl,

            "uuid_previous": [
            ],
            "version": 1,

        }
        if bulk:
            self.data["data"] = []
        else:
            self.set(data)
        self.data["uuid"] = str(uuid4())

    def appendBulk(self, event):
        '''Appends an event to this bulk event.

        Args:

            event(wishbone.event.Event): The event to add to the bulk instance

        Returns:

            None

        Raises:

            InvalidData: Either the event is not of type Bulk or <event> is
                         not an wishbone.event.Event instance.
        '''

        if self.data["bulk"]:
            if isinstance(event, Event):
                self.data["data"].append(event.dump())
            else:
                raise InvalidData("<event> should be of type wishbone.event.Event.")
        else:
            raise InvalidData("This instance is not initialized as a bulk event.")

    def clone(self):
        '''Returns a cloned version of the event.

        Args:

            None

        Returns:

            class: A ``wishbone.event.Event`` instance


        '''
        e = deepcopy(self)

        if "uuid_previous" in e.data:
            e.data["uuid_previous"].append(
                e.data["uuid"]
            )
        else:
            e.data["uuid_previous"] = [
                e.data["uuid"]
            ]
        e.data["uuid"] = str(uuid4())
        e.data["cloned"] = True

        return e

    def copy(self, source, destination):
        '''Copies the source key to the destination key.

        Args:

            source (str): The name of the source key.
            destination (str): The name of the destination key.
        '''

        self.set(
            deepcopy(
                self.get(
                    source
                )
            ),
            destination
        )

    def decrementTTL(self):
        '''Decrements the TTL value.

        Args:

            None

        Returns:

            None

        Raises:

            TTLExpired: When TTL has reached 0.
        '''

        if self.data["ttl"] == 0:
            raise TTLExpired("Event TTL expired in transit.")
        else:
            self.data["ttl"] -= 1

    def delete(self, key=None):
        '''Deletes a key.

        Args:

            key (str): The key to delete

        Returns:

            None

        Raises:

            Exception: Deleting the root of a reserved keyword such as <data> or <tags>.
            KeyError: When a non-existing key is referred to.
        '''

        s = key.split('.')
        if s[0] in EVENT_RESERVED and len(s) == 1:
            raise Exception("Cannot delete root of reserved keyword '%s'." % (key))

        if key is None:
            self.data = None
        else:
            if '.' in key:
                s = key.split('.')
                key = '.'.join(s[:-1])
                del(self.get(key)[s[-1]])
            else:
                del(self.data[key])

    def dump(self):
        '''Dumps the content of the event.

        Args:

            None

        Returns:

            dict: The content of the event.
        '''

        d = deepcopy(self)
        d.data["timestamp"] = str(d.data["timestamp"])
        return d.data

    def render(self, template, key="data"):
        '''Returns a formatted string using the provided template and key

        Args:

            template (str): A string representing the Jinja2 template.
            key (str): The name of key providing the values for the template

        Returns:

            str: The rendered string

        Raises:

            InvalidData: An invalid jinja2 template has been provided
        '''

        try:
            return Template(template).render(self.get(key))
        except Exception as err:
            raise InvalidData("Failed to render template. Reason: %s" % (err))

    def get(self, key="data"):
        '''Returns the value of <key>.

        Args:

            key (str): The name of the key to read.

        Returns:

            str/int/float/dict/list: The value of the key

        Raises:

            KeyError: The provided key does not exist.
        '''

        def travel(path, d):

            if len(path) == 1:
                if isinstance(d, dict):
                    return d[path[0]]
                else:
                    raise Exception()
            else:
                return travel(path[1:], d[path[0]])
        if key is None or key is "" or key is ".":
            return self.data
        else:
            try:
                path = key.split('.')
                data = travel(path, self.data)
                return data
            except Exception:
                raise KeyError(key)

    def has(self, key="data"):
        '''Returns a bool indicating the event has <key>

        Args:

            key (str): The name of the key to check

        Returns:

            bool: True if the key is there otherwise false

        Raises:

            KeyError: The provided key does not exist
        '''

        try:
            self.get(key)
        except KeyError:
            return False
        else:
            return True

    def set(self, value, key="data"):
        '''Sets the value of <key>.

        Args:

            value (str, int, float, dict, list): The value to assign.
            key (str): The key to store the value

        Returns:

            None

        '''
        result = value
        for name in reversed(key.split('.')):
            result = {name: result}

        self.__dictMerge(self.data, result)

    def slurp(self, data):
        '''Expects <data> to be a dict representation of an <Event> and
        alligns this event to it.

        The timestamp field will be reset to the time this method has been
        called.

        Args:

            data (dict): The dict object containing the complete event.

        Returns:

            wishbone.event.Event: A Wishbone event instance.


        Raises:

            InvalidEventFormat:  `data` does not contain valid fields to build
                                  an event
        '''

        try:
            assert isinstance(data, dict), "event.slurp() expects a dict."
            for item in [
                ("timestamp", int),
                ("version", int),
                ("data", None),
                ("tmp", dict),
                ("errors", dict),
                ("ttl", int),
            ]:
                assert item[0] in data, "%s is missing" % (item[0])
                if item[1] is not None:
                    assert isinstance(data[item[0]], item[1]), "%s type '%s' is not valid." % (item[0], item[1])
        except AssertionError as err:
            raise InvalidEventFormat("The incoming data could not be used to construct an event.  Reason: '%s'." % err)
        else:
            self.data = data
            self.data["timestamp"] = time.time()

    raw = dump

    def __dictMerge(self, dct, merge_dct):
        ''' Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
        updating only top-level keys, __dictMerge recurses down into dicts nested
        to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
        ``dct``.

        Stolen from https://gist.github.com/angstwad/bf22d1822c38a92ec0a9

        Args:

            dct(dict): The dictionary onto which the merge is executed
            merge_dct(dict: dict merged into `dct`

        Returns:

            dict: The merged version
        '''
        for k, v in list(merge_dct.items()):
            if k in dct and isinstance(dct[k], dict) and isinstance(merge_dct[k], dict):
                self.__dictMerge(dct[k], merge_dct[k])
            else:
                dct[k] = merge_dct[k]
