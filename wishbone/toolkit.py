#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  toolkit.py
#  
#  Copyright 2012 Jelle Smet development@smetj.net
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

import signal, sys
import logging
import stopwatch
from gevent import Greenlet, monkey
from gevent.queue import Queue
from gevent.event import Event
from gevent import sleep
from copy import deepcopy
monkey.patch_all()

class TimeFunctions(object):
    
    @classmethod
    def do(cls, fn):
        def do(self, *args, **kwargs):
            t = stopwatch.Timer()
            result = fn(self, *args, **kwargs)
            t.stop()
            try:
                self.metrics[fn.__name__]
            except:
                self.metrics[fn.__name__]={"total_time":0,"hits":0}
            self.metrics[fn.__name__]["total_time"] += t.elapsed
            self.metrics[fn.__name__]["hits"] += 1
            return result
        return do
    
    def timeConsume(self, fn, data):
        t = stopwatch.Timer()
        result = fn(data)
        t.stop()
        try:
            self.metrics[fn.__name__]
        except:
            self.metrics[fn.__name__]={"total_time":0,"hits":0}
        self.metrics[fn.__name__]["total_time"] += t.elapsed
        self.metrics[fn.__name__]["hits"] += 1
        return result
        
class QueueFunctions(TimeFunctions):
    '''A base class for Wishbone Actor classes.  Shouldn't be called directly but is inherited by PrimitiveActor.'''
    
    def __init__(self):
        self.inbox = Queue(None)
        self.outbox = Queue(None)
        self.metrics={}
    
    def sendData(self, data, queue='outbox'):
        '''Submits data to one of the module its queues.
        
        The data send by this funtion is automatically checked on integrity, whether it has the right Wishbone data structure.  If that is not the case
        an exception is returned.
        
        Parameters:

            * queue:  Determines to which queue data should be send.  By default this is 'outbox'.
        '''
        
        if self.checkIntegrity(data):
            try:
                getattr (self, queue).put ( data )
            except:
                setattr (self, queue, Queue)
                getattr (self, queue).put ( data )
        else:
            self.logging.warn('Invalid internal data structure detected. Data is purged. Turn on debugging to see datastructure.')
            self.logging.debug('Invalid data structure: %s' % (data))
    putData=sendData
    
    def sendRaw(self, data, queue='outbox'):
        '''Submits data to one of the module's queues.
        
        Allows you to bypass message integrity checking.  Its usage should be sparse, although it's usefull when you want to send data back 
        to a module as it would have come from the outside world.'''
        
        getattr (self, queue).put ( deepcopy(data) )
    putRaw=sendRaw
    
    def getData(self, queue="inbox"):
        '''Gets data from the queue.'''
        data = getattr (self, queue).get()
        return data
                
    def checkIntegrity(self, data):
        '''Checks the integrity of the messages passed over the different queues.
        
        The format of the messages should be:
        
        { 'headers': {}, data: {} }'''
        
        if type(data) is dict:
            if len(data.keys()) == 2:
                if data.has_key('header') and data.has_key('data'):
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
   
    def createQueue(self, name):
        
        try:
            setattr(self,name,Queue(None))
        except Exception as err:
            self.logging.warn('I could not create the queue named %s. Reason: %s'%(name, err))

class Block():
    '''A base class providing a global lock.'''
    
    def __init__(self):
        self.lock=Event()
        signal.signal(signal.SIGINT,self._ignoreSIGINT)
        
    def block(self):
        '''A simple blocking function.'''
        
        if self.lock.isSet():
            return False
        else:
            return True

    def wait(self, timeout=None):
        '''Blocks from exiting until self.lock is set.'''
        
        self.lock.wait(timeout)

    def release(self):
        '''Set the lock flag which essentially unlocks.'''
        
        self.lock.set()
    
    def _ignoreSIGINT(self,a,b):
        pass

class PrimitiveActor(Greenlet, QueueFunctions, Block):
    '''A base class used to create Wishbone modules.
    
    This base class offers Wishbone specific functionalities and objects.

    Parameters:
        name:      Gives a name to the module
    '''

    def __init__(self, name):
        Greenlet.__init__(self)
        QueueFunctions.__init__(self)
        Block.__init__(self)
        self.name=name
        self.metrics={}
        self.logging = logging.getLogger( name )
        self.logging.info('Initiated.')
         
    def _run(self):
        self.logging.info('Started.')        
        while self.block() == True:
            data = self.getData("inbox")
            self.timeConsume(self.consume, data)                            
        self.release()
                    
    def consume(self, *args, **kwargs):
        '''A function which should be overridden by the Wishbone module.
        
        This function, when called throws an exception.
        '''
        raise Exception ('You have no consume function in your class.')
    
    def shutdown(self):
        '''A function which could be overridden by the Wisbone module.
        
        This function is called on shutdown.  Make sure you include self.lock=False otherwise that greenthread will hang on shutdown and never exit.'''
        self.logging.info('Shutdown')
