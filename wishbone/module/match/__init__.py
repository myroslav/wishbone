#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  match.py
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


from wishbone import Actor
from gevent import spawn, sleep
from .matchrules import MatchRules
from .readrules import ReadRulesDisk


class Match(Actor):

    '''**Pattern matching on a key/value document stream.**

    This module routes messages to a queue associated to the matching rule
    set.  The event['data'] payload has to be of <type 'dict'>.  Typically,
    the source data is JSON converted to a Python dictionary.

    The match rules can be either stored on disk or directly defined into the
    bootstrap file.


    A match rule consists out of 2 parts:

        - condition:

        The condition part contains the individual conditions which have to
        match for the complete rule to match.

        re:     Regex matching
        !re:    Negative regex matching
        >:      Bigger than
        >=:     Bigger or equal than
        <:      Smaller than
        <=:     Smaller or equal than
        =:      Equal than
        in:     Evaluate list membership

        - queue:

        The queue section contains a list of dictionaries/maps each containing
        1 key with another dictionary/map as a value.  These key/value pairs
        are added to the *header section* of the event and stored under the
        queue name key.
        If you are not interested in adding any information to the header you
        can leave the dictionary empty.  So this would be valid:



    Examples
    ~~~~~~~~

    This example would route the events - with field "greeting" containing
    the value "hello" - to the outbox queue without adding any information
    to the header of the event itself.

    ::

        condition:
            "greeting": re:^hello$
        queue:
            - outbox:



    This example combines multiple conditions and stores 4 variables under
    event["header"][self.name] while submitting the event to the modules'
    **email** queue.

    ::

        condition:
            "check_command": re:check:host.alive
            "hostproblemid": re:\d*
            "hostgroupnames": in:tag:development

        queue:
            - email:
                from: monitoring@yourdomain.com
                to:
                    - oncall@yourdomain.com
                subject: UMI - Host  {{ hostname }} is  {{ hoststate }}.
                template: host_email_alert



    Parameters:

        - name(str)
           |  The name of the module.

        - size(int)
           |  The default max length of each queue.

        - frequency(int)
           |  The frequency in seconds to generate metrics.

        - location(str)(None)
           |  The directory containing rules.
           |  If none, no rules are read from disk.

        - rules(list)({})
           |  A list of rules in the above described format.


    Queues:

        - inbox
           |  Incoming events

        - <queue_name>
           |  The queue which matches a rule.

    '''

    def __init__(self, name, size=100, frequency=1, location=None, rules={}):
        Actor.__init__(self, name, size, frequency)
        self.location = location
        self.rules = rules
        self.__active_rules = {}
        self.match = MatchRules()
        self.pool.createQueue("inbox")
        self.registerConsumer(self.consume, "inbox")

    def preHook(self):

        self.__active_rules = self.rules
        if self.location is not None:
            self.logging.info("Rules directoy '%s' defined." % (self.location))
            spawn(self.getRules)

    def getRules(self):

        self.logging.info("Monitoring directory '%s' for changes" % (self.location))
        self.read = ReadRulesDisk(self.location)

        while self.loop():
            try:
                while self.loop():
                    self.__active_rules = dict(self.read.readDirectory().items() + self.rules.items())
                    self.logging.info("New set of rules loaded from disk")
                    break
                while self.loop():
                    self.__active_rules = dict(self.read.get().items() + self.rules.items())
                    self.logging.info("New set of rules loaded from disk")
            except Exception as err:
                self.logging.warning("Problem reading rules directory.  Reason: %s" % (err))
                sleep(1)

    def consume(self, event):
        '''Submits matching documents to the defined queue along with
        the defined header.'''

        for rule in self.__active_rules:
            if self.evaluateCondition(self.__active_rules[rule]["condition"], event["data"]):
                self.logging.debug("rule %s matches %s" % (rule, event["data"]))
                event["header"].update({self.name: {"rule": rule}})
                for queue in self.__active_rules[rule]["queue"]:
                    for name in queue:
                        if queue[name] is not None:
                            event["header"][self.name].update(queue[name])
                        self.submit(event, self.pool.getQueue(name))
                return
            else:
                self.logging.debug("Rule %s does not match event: %s" % (rule, event["data"]))

    def evaluateCondition(self, conditions, fields):
        for condition in conditions:
            if condition in fields:
                return self.match.do(conditions[condition], fields[condition])
        return False
