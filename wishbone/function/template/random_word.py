#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  random_word.py
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
import os
from random import choice
import io


class RandomWord(TemplateFunction):

    '''
    **Returns a random word.**

    This function returns a random word from a wordlist.  Each line is a new
    word.

    - Parameters to initialize the function:

        - filename(str)(None): When value is None, a buildin wordlist is used.
                               If not a filename of a wordlist is expected.

        - encoding(str)("latin-1"): The encoding used to read the file.


    - Parameters to call the function:

        None
    '''

    def __init__(self, filename=None, encoding="latin-1"):

        if filename is None:
            self.filename = "%s/../../data/wordlist.txt" % (os.path.dirname(__file__))
        else:
            self.filename = filename

        self.wordlist = self.readWordlist(filename, encoding)

    def readWordlist(self, location, encoding):
        with io.open(self.filename, encoding=encoding) as f:
            return f.readlines()

    def lookup(self):

        return choice(self.wordlist).rstrip()
