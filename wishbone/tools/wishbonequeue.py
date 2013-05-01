#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#
#
#  Copyright 2013 Jelle Smet <development@smetj.net>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
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

from mx.Queue import Queue, EmptyError
from gevent.event import Event
from itertools import count
from time import time

class WishboneQueue():
    def __init__(self, ack=False):
        self.__q=Queue()
        self.__acktable={}
        self.__ackticket=count()
        self.__in=0
        self.__out=0
        self.__ack=0
        self.__cache={}
        self.__lock=0
        self.__getlock=Event()
        if ack == True:
            self.get=self.__getAck
        else:
            self.get=self.__getNoAck

    def put(self, element):
        '''Puts element in queue'''
        if self.__lock != 1:
            self.__in+=1
            self.__q.push(element)
            self.__getlock.set()
        else:
            raise Exception ('Queue is locked.')

    def get(self):
        '''Gets an element from the queue.

        Points to self.__getNoAck or self.__getAck depending on init.'''

        pass

    def __getNoAck(self):
        '''Gets an element from the queue.

        Blocks when empty until an element is returned.'''

        if self.locked() == False:
            try:
                data = self.__q.pop()
                self.__out+=1
                return data
            except EmptyError:
                self.__getlock.clear()
                self.__getlock.wait()
        else:
            raise Exception ('The queue is locked.')

    def __getAck(self):
        '''Gets an element from the queue with acknowledgement.

        Blocks when empty until an element is returned.'''
        if self.locked() == False:
            data=self.__q.pop()
            ticket=next(self.__ackticket)
            self.__acktable[ticket]=data
            return (data,ticket)
        else:
            raise Exception ('The queue is locked.')

    def acknowledge(self, ticket):
        '''Acknowledges a previously consumed element.'''

        try:
            del(self.__acktable[ticket])
        except:
            return False

        self.__out+=1
        self.__ack+=1
        return True

    def cancel(self, ticket):
        '''Cancels an acknowledgement ticket.

        Returns the previously consumed element back to the queue.'''

        try:
            data = self.__acktable[ticket]
            del(self.__acktable[ticket])
            self.__q.push(data)
            return True
        except:
            return False

    def cancelAll(self):
        '''Cancels all acknoledgement tickets.

        All unacknowledged elements are send back to the queue.
        '''

        for event in self.__acktable.keys():
            self.__q.push(self.__acktable[event])
        self.__acktable={}

    def dump(self):
        '''Dumps and returns the queue in tuple format.
        '''
        help(self.__q)
        print self.__q.as_tuple()
        for event in self.__q.as_tuple():
            yield event

    def lock(self):
        '''Sets queue in locked state.

        When in locked state, elements can not be added or consumed.'''
        self.__getlock.set()
        self.__lock=1

    def locked(self):
        '''Returns whether the queue is in locked or unlocked state.

        True means locked, False means unlocked.

        '''

        if self.__lock==1:
            return True
        else:
            return False

    def unlock(self):
        '''Sets queue in unlocked state.

        When in unlocked state, elements can be added or consumed.'''
        self.__lock=0

    def size(self):
        '''Returns a tuple of the queue and unacknowledged the size of the queue.'''
        return (len(self.__q),len(self.__acktable))

    def empty(self):
        '''Returns True when queue and unacknowledged is empty otherwise False.'''

        if len(self.__q) > 0:
            return False
        else:
            return True

    def clear(self):
        '''Clears the queue.'''
        self.__q.clear()

    def stats(self):
        '''Returns statistics of the queue.'''
        return { "size":len(self.__q),
            "in_total":self.__in,
            "out_total":self.__out,
            "ack_total":self.__ack,
            "in_rate": self.__rate("in_rate",self.__in),
            "out_rate": self.__rate("out_rate",self.__out),
            "ack_rate":self.__rate("ack_rate",self.__ack)}

    def __rate(self, name, value):
        if not self.__cache.has_key(name):
            self.__cache[name]=(time(), value)
            return 0

        (timex, amount)=self.__cache[name]
        self.__cache[name]=(time(), value)
        #print "%s - %s"%(self.__cache[name][1], amount)
        return (self.__cache[name][1] - amount)/(self.__cache[name][0]-timex)