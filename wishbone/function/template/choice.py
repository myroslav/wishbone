#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  choice.py
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

from wishbone.function.template import TemplateFunction
from random import choice as choice_array


class Choice(TemplateFunction):
    '''
    Returns a random element from the provided array.

    A Wishbone template function which returns a random element from the
    provided array.

    Args:
        values (list): An array of elements to choose from
    '''

    def __init__(self, array):

        self.array = array

    def get(self):
        '''
        The function mapped to the template function.

        Args:
            None

        Returns:
            obj: An element of the provided array.
        '''

        return choice_array(self.array)
