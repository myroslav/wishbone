#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  modulemanager.py
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

import pkg_resources
import re
from prettytable import PrettyTable


class ModuleManager():

    def __init__(self):
        self.categories = ["wishbone", "wishbone.contrib"]
        self.groups = ["flow", "logging", "metrics", "function", "input", "output"]

    def listNames(self, category=None):

        if category is None:
            for category in self.categories:
                for group in self.groups:
                    group_name = "%s.%s" % (category, group)
                    for m in pkg_resources.iter_entry_points(group=group_name):
                        yield (category, group, m.name)

    def getModule(self, category, group, name):

        return pkg_resources.load_entry_point("wishbone", "%s.%s" % (category, group), name)

    def getModuleDoc(self, category, group, name):

        doc = self.getModule(category, group, name).__doc__
        doc = re.search('(\*\*.*?\*\*)(.*)', doc).group(2)
        return doc

    def getModuleTitle(self, category, group, name):

        doc = self.getModule(category, group, name).__doc__
        title = re.search('\*\*(.*?)\*\*(.*)', doc).group(1)
        return title

    def getModuleTable(self, category=None, group=None):

        table = self.__getTable()

        category_header = None
        group_header = None
        for (category, group, module) in self.listNames():
            title = self.getModuleTitle(category, group, module)
            version = self.getModuleVersion(category, group, module)
            if category_header == category:
                category = ""
            else:
                category_header = category
            if group_header == group:
                group = ""
            else:
                table.add_row(["", "", "", "", ""])
                group_header = group
            table.add_row([category, group, module, version, title])

        return table.get_string()

    def getModuleVersion(self, category, group, name):

        try:
            return pkg_resources.get_entry_info(category, "%s.%s" % (category, group), name).dist.version
        except:
            return "?"

    def __getTable(self):

        t = PrettyTable(["Category", "Group", "Module", "Version", "Description"])
        t.align["Category"] = "l"
        t.align["Group"] = "l"
        t.align["Module"] = "l"
        t.align["Version"] = "r"
        t.align["Description"] = "l"

        return t
