#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  configfile.py
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

import yaml
from easydict import EasyDict
from jsonschema import validate

SCHEMA = {
    "type": "object",
    "properties": {
        "protocols": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "protocol": {
                            "type": "string"
                        },
                        "arguments": {
                            "type": "object"
                        }
                    },
                    "required": ["protocol"],
                    "additionalProperties": False,
                },
            },
        },
        "module_functions": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "function": {
                            "type": "string"
                        },
                        "arguments": {
                            "type": "object"
                        }
                    },
                    "required": ["function"],
                    "additionalProperties": False
                }
            }
        },
        "template_functions": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "function": {
                            "type": "string"
                        },
                        "arguments": {
                            "type": "object"
                        }
                    },
                    "required": ["function"],
                    "additionalProperties": False
                }
            }
        },
        "modules": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "module": {
                            "type": "string"
                        },
                        "protocol": {
                            "type": "string"
                        },
                        "description": {
                            "type": "string"
                        },
                        "arguments": {
                            "type": "object"
                        },
                        "functions": {
                            "type": "object"
                        },
                        "event": {
                            "type": "boolean"
                        }
                    },
                    "required": ["module"],
                    "additionalProperties": False
                }
            }
        },
        "routingtable": {
            "type": "array"
        }
    },
    "required": ["modules", "routingtable"],
    "additionalProperties": False
}

LOG_TEMPLATE = '''
    {%- if data.level == 0 -%}
        \x1B[0;35m
    {%- elif data.level == 1 -%}
        \x1B[1;35m
    {%- elif data.level == 2 -%}
        \x1B[0;31m
    {%- elif data.level == 3 -%}
        \x1B[1;31m
    {%- elif data.level == 4 -%}
        \x1B[1;33m
    {%- elif data.level == 5 -%}
        \x1B[1;30m
    {%- elif data.level == 6 -%}
        \x1B[1;37m
    {%- else -%}
        \x1B[1;37m
    {%- endif -%}
    {{strftime(epoch(), "YYYY-MM-DDTHH:mm:ss.SSSSZZ")}} {{data.identification}}[{{data.pid}}] {{data.txt_level}} {{data.module}}: {{data.message}}\x1B[0m'''


class ConfigFile(object):

    '''Generates a wishbone.router configuration object used to initialize a
    wishbone router object.

    Args:
        filename (str): The filename of the configuration to load.
        logstyle (str): How logging should be setup. Possible options are: stdout and syslog.
        loglevel (str): The loglevel for the router to use to use.
        identification (str): A string which identifies the router instance
        colorize_stdout (bool): When True, colors each stdout printed logline using proper coloring.
    '''

    def __init__(self, filename, logstyle, loglevel=6, identification="wishbone", colorize_stdout=True):
        self.identification = identification
        self.colorize_stdout = colorize_stdout
        self.logstyle = logstyle
        self.loglevel = loglevel
        self.config = EasyDict({
            "template_functions": EasyDict({}),
            "modules": EasyDict({}),
            "module_functions": EasyDict({}),
            "protocols": EasyDict({}),
            "routingtable": []
        })
        self.__addLogFunnel()
        self.__addMetricFunnel()
        self.load(filename)

    def addModule(self, name, module, arguments={}, description="", functions={}, protocol=None, event=False):

        if name.startswith('_'):
            raise Exception("Module instance names cannot start with _.")

        self.__addModule(name, module, arguments, description, functions, protocol, event)

    def addTemplateFunction(self, name, function, arguments={}):

        if name not in self.config["template_functions"]:
            self.config["template_functions"][name] = EasyDict({
                "function": function,
                "arguments": arguments
            })
        else:
            raise Exception("Lookup instance name '%s' is already taken." % (name))

    def addModuleFunction(self, name, function, arguments={}):

        self.config["module_functions"][name] = EasyDict({"function": function, "arguments": arguments})

    def addProtocol(self, name, protocol, arguments={}, event=False):

        self.config["protocols"][name] = EasyDict({"protocol": protocol, "arguments": arguments, "event": event})

    def addConnection(self, source_module, source_queue, destination_module, destination_queue):

        connected = self.__queueConnected(source_module, source_queue)

        if not connected:
            self.config["routingtable"].append(
                EasyDict({
                    "source_module": source_module,
                    "source_queue": source_queue,
                    "destination_module": destination_module,
                    "destination_queue": destination_queue
                })
            )
        else:
            raise Exception("Cannot connect '%s.%s' to '%s.%s'. Reason: %s." % (source_module, source_queue, destination_module, destination_queue, connected))

    def dump(self):

        return EasyDict(self.config)

    def load(self, filename):

        config = self.__load(filename)
        self.__validate(config)
        self.__validateRoutingTable(config)

        if "template_functions" in config:
            for function in config["template_functions"]:
                self.addTemplateFunction(name=function, **config["template_functions"][function])

        if "module_functions" in config:
            for function in config["module_functions"]:
                self.addModuleFunction(name=function, **config["module_functions"][function])

        if "protocols" in config:
            for protocol in config["protocols"]:
                self.addProtocol(
                    name=protocol,
                    protocol=config["protocols"][protocol].get("protocol", None),
                    arguments=config["protocols"][protocol].get("arguments", {}),
                    event=config["protocols"][protocol].get("event", False)
                )

        for module in config["modules"]:
            self.addModule(name=module, **config["modules"][module])

        for route in config["routingtable"]:
            sm, sq, dm, dq = self.__splitRoute(route)
            self.addConnection(sm, sq, dm, dq)

        getattr(self, "_setupLogging%s" % (self.logstyle.upper()))()

    def __addModule(self, name, module, arguments={}, description="", functions={}, protocol=None, event=False):

        if protocol is not None and protocol not in self.config.protocols:
            raise Exception("No protocol module defined with name '%s' for module instance '%s'" % (protocol, name))

        for queue, fs in functions.items():
            for function in fs:
                if function not in self.config.module_functions.keys():
                    raise Exception("No function defined with name '%s' for module instance '%s'." % (function, name))

        if name not in self.config["modules"]:
            self.config["modules"][name] = EasyDict({
                'description': description,
                'module': module,
                'arguments': arguments,
                'functions': functions,
                'protocol': protocol,
                'event': event})
            self.addConnection(name, "_logs", "_logs", "_%s" % (name))
            self.addConnection(name, "_metrics", "_metrics", "_%s" % (name))

        else:
            raise Exception("Module instance name '%s' is already taken." % (name))

    def __queueConnected(self, module, queue):

        for c in self.config["routingtable"]:
            if (c["source_module"] == module and c["source_queue"] == queue) or (c["destination_module"] == module and c["destination_queue"] == queue):
                return "Queue '%s.%s' is already connected to '%s.%s'" % (c["source_module"], c["source_queue"], c["destination_module"], c["destination_queue"])
        return False

    def __splitRoute(self, route):

        (source, destination) = route.split('->')
        (source_module, source_queue) = source.rstrip().lstrip().split('.')
        (destination_module, destination_queue) = destination.rstrip().lstrip().split('.')
        return source_module, source_queue, destination_module, destination_queue

    def __load(self, filename):
        '''Loads and returns the yaml bootstrap file.'''

        try:
            with open(filename, 'r') as f:
                config = yaml.load(f)
        except Exception as err:
            raise Exception("Failed to load bootstrap file.  Reason: %s" % (err))
        else:
            return config

    def __validate(self, config):

        try:
            validate(config, SCHEMA)
        except Exception as err:
            raise Exception("Failed to validate configuration file.  Reason: %s" % (err.message))

    def __validateRoutingTable(self, config):

        for route in config["routingtable"]:
            (left, right) = route.split("->")
            assert "." in left.lstrip().rstrip(), "routingtable rule \"%s\" does not have the right format. Missing a dot." % (route)
            assert "." in right.lstrip().rstrip(), "routingtable rule \"%s\" does not have the right format. Missing a dot." % (route)

    def __addLogFunnel(self):

        self.__addModule(
            name="_logs",
            module="wishbone.module.flow.funnel",
            arguments={
            },
            description="Centralizes the logs of all modules.",
            functions={
            },
            protocol=None
        )

    def __addMetricFunnel(self):

        self.__addModule(
            name="_metrics",
            module="wishbone.module.flow.funnel",
            arguments={
            },
            description="Centralizes the metrics of all modules.",
            functions={
            },
            protocol=None
        )

    def _setupLoggingSTDOUT(self):

        self.addTemplateFunction("strftime", "wishbone.function.template.strftime")
        self.addTemplateFunction("epoch", "wishbone.function.template.epoch")

        if not self.__queueConnected("_logs", "outbox"):

            self.__addModule(
                name="_logs_format",
                module="wishbone.module.process.template",
                arguments={
                    "templates": {
                        "human_log": LOG_TEMPLATE
                    }
                },
                description="Create a human readable log format.",
                functions={
                },
                protocol=None
            )
            self.addConnection("_logs", "outbox", "_logs_format", "inbox")

            self.__addModule(
                name="_logs_stdout",
                module="wishbone.module.output.stdout",
                arguments={
                    "colorize": self.colorize_stdout,
                    "selection": "human_log"
                },
                description="Prints all incoming logs to STDOUT.",
                functions={
                },
                protocol=None
            )
            self.addConnection("_logs_format", "outbox", "_logs_stdout", "inbox")

    def _setupLoggingSYSLOG(self):

        if not self.__queueConnected("_logs", "outbox"):

            self.__addModule(
                name="_logs_syslog",
                module="wishbone.module.output.syslog",
                arguments={
                    "ident": self.identification,
                    "payload": "module({{data.module}}): {{data.message}}"
                },
                description="Writes all incoming messages to syslog.",
                functions={
                },
                protocol=None
            )
            self.addConnection("_logs", "outbox", "_logs_syslog", "inbox")
