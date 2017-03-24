#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  encode_msgpack.py
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


def encodeMSGPackWrapper(source='@data', destination='@data', *args, **kwargs):
    '''
    **Encode MSGPack**

    Converts a Python data structure into a MSGPack binary blob.

    Parameters:

        n/a
    '''

    from msgpack import packb

    def encodeMSGPack(event):
        event.set(packb(event.get(source)), destination)
        return event

    return encodeMSGPack
