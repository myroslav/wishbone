#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       broker_loopback.py
#       
#       Copyright 2012 Jelle Smet development@smetj.net
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#       
#       

from wishbone.toolkit import PrimitiveActor


class BrokerLoopback(PrimitiveActor):
    '''The BrokerLoopback class does nothing more than adding broker data to the headers of each message and writes that back to its
    outgoing queue.
    '''
    
    def __init__(self, name, *args, **kwargs):
        '''

        * key       :   The routing key to which to send incoming data.
                        Default: name
                        Type: string
        
        * exchange  :   The exchange to write data to.
                        Default: ''
                        Type: string
                            
        '''
        PrimitiveActor.__init__(self, name)
        self.key = kwargs.get('key',name)
        self.exchange = kwargs.get('exchange','')
    
    def consume(self,doc):
        doc['header']['broker_key']=self.key
        doc['header']['broker_exchange']=self.exchange
        self.sendData(doc)
       
    def shutdown(self):
        self.logging.info('Shutdown')
