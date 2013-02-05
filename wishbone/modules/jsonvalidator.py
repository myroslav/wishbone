#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       jsonvalidator.py
#       
#       Copyright 2013 Jelle Smet development@smetj.net
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
#       #       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#       
#       

import json
from jsonschema import Validator
from wishbone.toolkit import PrimitiveActor, TimeFunctions


class JSONValidator(PrimitiveActor, TimeFunctions):
    '''**A Wishbone module which verifies JSON data against a validator schema loaded from file.**
    
    Events consumed from the inbox queue are verified against a Validator schema.  When the event is not a valid JSON document
    or when it doesn't match your predifined Validator schema, it is dropped.

    Parameters:        
    
        - name (str):       The instance name when initiated.    
        - schema (str):     The location and filename of the schema to load.  The schema should follow http://json-schema.org/ specifications.
        - convert (bool):   When True it will aditionally convert the incoming JSON string to a Python object.
        
        
    Queues:        

        - inbox:    Incoming events.
        - outbox:   Outgoing events.
    '''    
    
    def __init__(self, name, schema=False, convert=False):
        PrimitiveActor.__init__(self, name)
        self.name = name
        self.schema = schema
        self.convert = convert
        (self.validator, self.validator_schema) = self.loadValidator(schema)

    def loadValidator(self,schema):
        '''Loads the json-schema definition from disk.'''
        if schema == False:
            self.logging.info("No schema defined, no schema loaded, no validation.")
            return (False, False)
        else:
            file = open(self.schema,'r')
            data = file.readlines()
            file.close()
            return (Validator(), json.loads(''.join(data)))

    def consume(self, message):
        '''Executed for each incoming message.'''
        
        try:
            data = json.loads(message["data"])
            self.validate(data)
            if self.convert == True:
                message['data']=data
            self.putData(message)
        except Exception as err:
            self.logging.warning('Invalid data received and purged. Reason: %s' % (err))
    
    @TimeFunctions.do
    def validate(self,data):
        '''Validates data against the JSON schema.'''
        if self.validator == False:
            return True
        else:
            self.validator.validate(data,self.validator_schema)
