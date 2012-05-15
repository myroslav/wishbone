#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  server.py
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

import logging
import daemon
from multiprocessing import Process, Event
from time import sleep
from os import getpid, kill, remove
import sys

class Server():
    '''Handles starting, stopping and daemonizing of one or multiple Wishbone instances.''' 
    
    def __init__(self, instances=1, setup=None, daemonize=False, log_level=logging.INFO, name='Server'):
        self.instances=instances
        self.setup=setup
        self.daemonize=daemonize
        self.log_level=log_level
        self.name=name
        self.pidfile='/tmp/%s.pid'%name
        self.wishbone=None
        self.processes=[]
        self.pids = []
    
    def start(self):
        '''Starts the server environment in fore- or background.'''
                
        if self.checkPids() != False:
            if self.daemonize == True:
                print 'Starting %s in background.' % (self.name)
                self.configureLogging(name=self.name, syslog=True)
                self.logging = logging.getLogger( 'Server' )
                with daemon.DaemonContext():
                    self.__start()
            else:
                self.configureLogging()
                self.logging = logging.getLogger( 'Server' )
                self.__start()
    
    def __start(self):
        '''Actually starts the environment.  Should only be called by self.start().'''
        
        for number in range(self.instances):
            self.processes.append(Process(target=self.setup, name=number))
            self.processes[number].start()
            self.logging.info('Instance #%s started.'%number)
        
        self.pids = self.collectPids()
        self.writePids()
        self.logging.info('Started with pids: %s' % ', '.join(map(str, self.pids)))
        
        try:
            while True:
                sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        '''Stops the environment.'''
        
        self.logging.info('SIGINT received. Stopping')
        for process in self.processes:
            self.logging.info('Waiting for %s' %process.name)
            try:
                process.join()
            except KeyboardInterrupt:
                #some people have no patience
                process.terminate()
                
        logging.shutdown()

    def collectPids(self):
        '''Gets the pids of the current process and all the ones started by multiprocessing.'''
        
        pids = [getpid()]
        for process in self.processes:
            pids.append(process.pid)
        return pids
    
    def checkPids(self):
        '''Reads the pids of the pidfile.'''
        
        try:
            pidfile = open (self.pidfile,'r')
            for pid in pidfile.readlines():
                try:
                    kill(int(pid),0)
                except:
                    pass
                else:
                    print 'There is already a version of %s running with pid %s' % (self.name, pid)
                    pidfile.close()
                    sys.exit(1)
            pidfile.close()
            try:
                remove(self.pidfile)
                self.logging.warn('Pidfile exists, but processes not running anymore. Removed.')
            except Exception as err:
                self.logging.warn('Pidfile exists, but I could not remove it.  Reason: %s' % (err))
                sys.exit(1)
        except:
            pass
        
        return False
        
    def writePids(self):
        '''Writes all the pids into a pid file.
        
        The name of the file is set at __init__()  If no absolute filename is given server.pid is chosen in the current path.'''
        
        try:
            pidfile = open(self.pidfile,'w')
            pidfile.write("\n".join(map(str, self.pids)))
            pidfile.close()
        except Exception as err:
            self.logging.warn('Could not write pid file.  Reason: %s' %(err))
            
    
    def configureLogging(self,name=None, syslog=False, loglevel=logging.INFO):
        '''Configures logging.
        
        Configures the format of the logging messages.  This function accepts 1 parameter:
        
        loglevel: defines the loglevel.'''
        
        if name == None:
            format= '%(asctime)s %(levelname)s %(name)s: %(message)s'
        else:
            format= name+' %(name)s: %(message)s'
        if syslog == False:
            logging.basicConfig(level=loglevel, format=format)
        else:
            from logging.handlers import SysLogHandler
            logger = logging.getLogger()
            logger.setLevel(loglevel)
            syslog = SysLogHandler(address='/dev/log')
            syslog.set_name(self.name)
            formatter = logging.Formatter(format)
            syslog.setFormatter(formatter)
            logger.addHandler(syslog)

