#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  actor.py
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

from wishbone.queue import QueuePool
from wishbone.logging import Logging
from wishbone.event import Event as Wishbone_Event
from wishbone.error import ModuleInitFailure, InvalidModule, TTLExpired, InvalidData
from wishbone.moduletype import ModuleType
from wishbone.actorconfig import ActorConfig
from wishbone.function.template import TemplateFunction
from wishbone.function.module import ModuleFunction

from collections import namedtuple
from gevent import spawn, kill
from gevent import sleep, socket
from gevent.event import Event
from wishbone.error import QueueFull
from time import time
from sys import exc_info
import traceback
import inspect
import jinja2

from easydict import EasyDict


Greenlets = namedtuple('Greenlets', "consumer generic log metric")


class RenderKwargs(object):
    '''
    Keeps a rendered versions of kwargs templates relative to events consumed
    from different queues.

    Args:
        data (dict): A dict representing the raw unprocessed kwargs.
        functions (dict): A dict Jinja2 template functions.
    '''

    def __init__(self, data, functions={}):

        self.env_template = jinja2.Environment(
            undefined=jinja2.StrictUndefined,
            trim_blocks=True,
            loader=jinja2.FileSystemLoader('/')
        )
        self.env_template.globals.update(functions)
        self.__original_kwargs = data
        self.template_strings = {}
        self.__template_kwargs = self.__initialize_templates(data, functions)
        self.__rendered_kwargs = {}
        self.render(None, {})
        self.functions = functions

    def get(self, key, queue_context=None):
        '''
        Returns the rendered kwarg value within the given queue_context.

        Args:
            key (str): The key to return. (can be dotted notation for nested dicts)
            queue_context (str): The name of the queue

        Returns:
            The rendered version of the values stored under `key`.

        '''

        if queue_context not in self.__rendered_kwargs:
            raise InvalidData("No kwargs have been rendered yet for queue '%s'." % (queue_context))
        else:
            result = self.__lookup(key, self.__rendered_kwargs[queue_context])
            if result is None:
                return None
            else:
                return result

    def render(self, queue_context=None, event_content={}):
        '''
        Renders the kwargs values using the provided payload.

        Args:
            queue_context (str): The name of the queue to store the results
            event_content (dict): The key values to feed to the templates.

        Returns:
            None

        Todo:
            * Opportunity to optimize here?
        '''

        def recurse(data):

            if isinstance(data, jinja2.environment.Template):
                try:
                    return data.render(**event_content)
                except Exception as err:
                    return "#error: %s#" % (err)
                    # return self.template_strings[data]
            elif isinstance(data, dict):
                result = {}
                for key, value in data.items():
                    result[key] = recurse(value)
                return EasyDict(result)
            elif isinstance(data, list):
                result = []
                for value in data:
                    result.append(recurse(value))
                return result
            else:
                return data

        rendered_kwargs = EasyDict(
            recurse(
                self.__template_kwargs.copy()
            )
        )

        self.__rendered_kwargs[queue_context] = rendered_kwargs
        return rendered_kwargs

    def __initialize_templates(self, kwargs, functions):

        def recurse(data):

            if isinstance(data, str):
                try:
                    if len(list(self.env_template.parse(data).find_all(jinja2.nodes.Name))) > 0:
                        t = self.env_template.from_string(data)
                        self.template_strings[t] = data
                        return t
                    else:
                        return data
                except Exception as err:
                    return data

            elif isinstance(data, dict):
                for key, value in data.items():
                    data[key] = recurse(value)
                return data
            elif isinstance(data, list):
                for index, value in enumerate(data):
                    data[index] = recurse(value)
                return data
            else:
                return data

        result = recurse(kwargs)
        return result

    def __lookup(self, key, dataset):

        def recurse(skey, data):
            value = data[skey[0]]
            if len(skey) == 1:
                return value
            else:
                return recurse(skey[1:], value)

        return recurse(key.split('.'), dataset)


class Actor(object):
    """A base class providing core Actor functionality.

    The Actor base class is responsible for providing the base functionality,
    setup and helper functions of a Wishbone module.

    Args:
        config (wishbone.actorconfig.ActorConfig): The ActorConfig object instance.

    Attributes:
        config (wishbone.actorconfig.ActorConfig): The ActorConfig object instance.
        name (str): The name of the instance, derived from `config`.
        description (str): The description of the actor based instance, derived from `config`.

                pool (wishbone.pool.QueuePool): The Actor's queue pool.
    Methods:
        logging (wishbone.logging.Logging)

    """

    def __init__(self, config):

        self.config = config
        self.name = config.name
        self.description = self.__getDescription(config)

        self.pool = QueuePool(config.size)

        self.logging = Logging(
            name=config.name,
            q=self.pool.queue._logs,
            identification=self.config.identification
        )

        self.__loop = True
        self.greenlets = Greenlets([], [], [], [])
        self.greenlets.metric.append(spawn(self.__metricProducer))

        self.__run = Event()
        self.__run.clear()

        self.stopped = True

        self.__renderKwargs = self.__setupRenderKwargs()
        self.renderKwargs()
        self.__setupValidation()

    def generateEvent(self, data={}):
        '''
        Generates a new event.

        This function gets overwritten by either
        ``self.__generateNormalEvent`` or ``self.__reconstructEvent``.

        Args:
            data (``data``): The payload to add to the event.

        Returns:
            wishbone.event.Event: An event containing ``data`` as a payload.

        '''

        raise ModuleInitFailure("Function should get overwritten by either self.__generateNormalEvent or self.__reconstructEvent.")

    def loop(self):
        '''The global lock for this module.

        Returns:
            bool: True when module is in running mode. False if not.
        '''

        return self.__loop

    def postHook(self):
        '''
        Is executed when module exits.
        '''

        self.logging.debug("Module has no postHook() method set.")

    def preHook(self):
        '''
        Is executed when module starts.
        '''

        self.logging.debug("Module has no preHook() method set.")

    def registerConsumer(self, function, queue):
        '''
        Registers <function> to process all events in <queue>

        Don't not trap errors here.  When <function> fails then the event will be
        submitted to the "failed" queue,  If <function> succeeds to the
        success queue.

        Args:
            function (``function``): The function which processes events
            queue (str): The name of the queue from which ``function`` will
                         process the events.

        Returns:
            None
        '''

        self.greenlets.consumer.append(spawn(self.__consumer, function, queue))

    def renderEventKwargs(self, event, queue=None):
        '''
        Renders kwargs using the content of ``event`` and stores the result under
        ``event.kwargs``.

        Args:
            event (``wishbone.event.Event``): An Event instance
            queue (str): The queue name so ``RenderKwargs`` can store the results
                         in the correct queue context.

        Returns:
            ``wishbone.event.Event``: The provided event instance.
        '''

        event.kwargs = self.__renderKwargs.render(
            queue_context=queue,
            event_content=event.dump()
        )
        return event

    def renderKwargs(self):
        '''
        Renders kwargs without making use of event content. This is typically
        used when initiliazing a module and render the defined kwargs which do
        not need a event data for rendering.

        Returns:
            None
        '''

        self.kwargs = self.__renderKwargs.render()

    def start(self):
        '''
        Starts the module.

        Returns:
            None
        '''

        self.__setProtocolMethod()

        if hasattr(self, "preHook"):
            self.logging.debug("preHook() found, executing")
            self.preHook()
        self.__validateAppliedFunctions()
        self.__run.set()
        self.logging.debug(
            "Started with max queue size of %s events and metrics interval of %s seconds." % (
                self.config.size,
                self.config.frequency
            )
        )
        self.stopped = False

    def sendToBackground(self, function, *args, **kwargs):
        '''

        Executes a function and sends it to the background. Such a function
        should never exit until ``self.loop`` returns ``False``.
        This `method` wraps ``function`` again in a loop as long ``self.loop``
        returns ``False`` so that ``function`` is restarted and an error is
        logged.

        Args:
            function (``function``): The function which has to be executed.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        '''

        def wrapIntoLoop():
            while self.loop():
                try:
                    function(*args, **kwargs)
                    # We want to break out of the loop if we get here because
                    # it's the intention of function() to exit without errors.
                    # Normally, background tasks run indefinately but in this
                    # case the user opted not to for some reason so we should
                    # obey that.
                    break
                except Exception as err:
                    if self.config.disable_exception_handling:
                        raise
                    self.logging.error("Backgrounded function '%s' of module instance '%s' caused an error. This needs attention. Restarting it in 2 seconds. Reason: %s" % (
                        function.__name__,
                        self.name,
                        err)
                    )
                    sleep(2)

        self.greenlets.generic.append(spawn(wrapIntoLoop))

    def stop(self):
        '''
        Makes ``self.loop`` return ``False`` and handles shutdown of of the
        registered background jobs.
        '''

        self.logging.info("Received stop. Initiating shutdown.")

        self.__loop = False

        for background_job in self.greenlets.metric:
            kill(background_job)

        for background_job in self.greenlets.generic:
            kill(background_job)

        for background_job in self.greenlets.consumer:
            kill(background_job)

        if hasattr(self, "postHook"):
            self.logging.debug("postHook() found, executing")
            self.postHook()

        self.logging.debug("Exit.")

        self.stopped = True

    def submit(self, event, queue):
        '''
        Submits <event> to the queue with name <queue>.


        Args:
            event (wishbone.event.Event): An event instance.
            queue (str): The name of the queue

        Returns:
            None
        '''

        while self.loop():
            try:
                getattr(self.pool.queue, queue).put(event)
                break
            except AttributeError:
                self.logging.error("No such queue %s. Event with uuid %s dropped." % (queue, event.get('uuid')))
                break
            except QueueFull:
                self.logging.warning("Queue '%s' is full and stalls the event pipeline. You should probably look into this." % (queue))
                sleep(0.1)

    def __applyFunctions(self, queue, event):

        '''
        Executes and applies all registered module functions against the event.

        Args:
            queue (str): The name of the queue to which the function was registered.
            event (wishbone.event.Event): The Wishbone

        Returns:
            wisbone.event.Event: The modified version of ``event``
        '''

        if queue in self.config.module_functions:
            for f in self.config.module_functions[queue]:
                try:
                    event = f(event)
                except Exception as err:
                    if self.config.disable_exception_handling:
                        raise
                    self.logging.error("Function '%s' is skipped as it is causing an error. Reason: '%s'" % (f.__name__, err))
        return event

    def __consumer(self, function, queue):
        '''
        Greenthread which applies <function> to each element from <queue>

        Args:
            function (``function``): The function which has been registered to consume ``queue``.

            queue (str): The name of the queue from which events have to be
                         consumed and processed by ``function``.

        Returns:
            None
        '''

        self.__run.wait()
        self.logging.debug("Function '%s' has been registered to consume queue '%s'" % (function.__name__, queue))

        while self.loop():

            event = self.pool.getQueue(queue).get()

            # Render kwargs relative to the event's content and make these accessible under event.kwargs
            event = self.renderEventKwargs(event=event, queue=queue)

            # Validate TTL
            try:
                event.decrementTTL()
            except TTLExpired as err:
                self.logging.warning("Event with UUID %s dropped. Reason: %s" % (event.get("uuid"), err))
                continue

            # Set the current event uuid to the logger object
            self.logging.setCurrentEventID(event.get("uuid"))

            # Apply all the defined queue functions to the event
            event = self.__applyFunctions(queue, event)

            # Apply consumer function
            try:
                function(event)
            except Exception as err:
                if self.config.disable_exception_handling:
                    raise
                exc_type, exc_value, exc_traceback = exc_info()
                info = (traceback.extract_tb(exc_traceback)[-1][1], str(exc_type), str(exc_value))

                event.set(info, "errors.%s" % (self.name))

                self.logging.error("%s" % (err))
                self.submit(event, "_failed")
            else:
                self.submit(event, "_success")
            finally:
                # Unset the current event uuid to the logger object
                self.logging.setCurrentEventID(None)

    def __generateNormalEvent(self, data={}):
        '''
        Gets mapped to self.generateEvent for `flow`, `process` and `output` type modules.

        Args:
            data (``data``): The payload to add to the event.

        Returns:
            wishbone.event.Event: An event containing ``data`` as a payload.
        '''

        return Wishbone_Event(data)

    def __getDescription(self, config):
        '''
        Gets the module description.

        Args:
            config (``wishbone.actorconfig.ActorConfig``): An ActorConfig instance

        Returns:
            str: The description of this actor instance.
        '''


        if config.description is None:
            return self.__doc__.strip().split('\n')[0].strip('*')
        else:
            return config.description

    def __reconstructEvent(self, data={}):
        '''

        Gets mapps to self.generateEvent for `input` type modules and if
        ``Actor.config.protocol_event`` is ``True``.

        Args:
            data (dict): The dict representation of ``wishbone.event.Event``.

        Returns:
            wishbone.event.Event: ``Event`` instance of ``data``
        '''

        e = Wishbone_Event()
        e.slurp(data)
        return e

    def __metricProducer(self):
        '''
        A greenthread collecting the queue metrics at the defined interval.
        '''

        self.__run.wait()
        hostname = socket.gethostname()
        while self.loop():
            for queue in self.pool.listQueues(names=True):
                for metric, value in list(self.pool.getQueue(queue).stats().items()):
                    event = Wishbone_Event({
                        "time": time(),
                        "type": "wishbone",
                        "source": hostname,
                        "name": "module.%s.queue.%s.%s" % (self.name, queue, metric),
                        "value": value,
                        "unit": "",
                        "tags": ()
                    })
                    self.submit(event, "_metrics")
            sleep(self.config.frequency)

    def __setProtocolMethod(self):
        '''
        Sets a ``self.encode`` for `output` modules or ``self.decode`` for
        `input` modules.
        '''

        if not hasattr(self, "MODULE_TYPE"):
            raise InvalidModule("Module instance '%s' seems to be of an incompatible old type." % (self.name))

        if self.MODULE_TYPE == ModuleType.INPUT:
            if not hasattr(self, "decode") and self.config.protocol_name is None:
                self.logging.debug("This 'Input' module has no decoder method set. Setting dummy decoder.")
                self.setDecoder("wishbone.protocol.decode.dummy")
            if self.config.protocol_name is not None:
                self.logging.debug("This 'Input' module has '%s' decoder configured." % (self.config.protocol_name))
                self.decode = self.config.protocol_function

            if self.config.protocol_event is True:
                self.generateEvent = self.__reconstructEvent
            else:
                self.generateEvent = self.__generateNormalEvent

        if self.MODULE_TYPE == ModuleType.OUTPUT:
            if not hasattr(self, "encode") and self.config.protocol_name is None:
                self.logging.debug("This 'Output' module has no encoder method set. Setting dummy encoder.")
                self.setEncoder("wishbone.protocol.encode.dummy")
            if self.config.protocol_name is not None:
                self.logging.debug("This 'Output' module has '%s' encoder configured." % (self.config.protocol_name))
                self.encode = self.config.protocol_function

    def __setupRenderKwargs(self):
        '''
        Initial rendering of all templates to self.kwargs
        '''

        kwargs = {}
        for key, value in list(inspect.getouterframes(inspect.currentframe())[2][0].f_locals.items()):
            if key == "self" or isinstance(value, ActorConfig):
                next
            else:
                kwargs[key] = value

        functions = {}
        for n, f in self.config.template_functions.items():
            functions[n] = f.get

        return RenderKwargs(kwargs, functions)

    def __validateAppliedFunctions(self):
        '''
        A validation routine which checks whether functions have been applied
        to queues without a registered consumer.  The effect of that would be
        that the functions are never applied which is not what the user
        wanted.
        '''

        queues_w_registered_consumers = [t.args[1] for t in self.greenlets.consumer]

        for queue in self.config.module_functions.keys():
            if queue not in queues_w_registered_consumers:
                raise ModuleInitFailure("Failed to initialize module '%s'. You have functions defined on queue '%s' which doesn't have a registered consumer." % (self.name, queue))

    def __setupValidation(self):
        '''
        Does following validations:

            - Validate if all template functions base ``TemplateFunction``
            - Validate if all module functions base ``ModuleFunction``
            - Validate if ``ModuleType.OUTPUT`` has ``payload`` and ``selection`` parameter.

        Args:
            None

        Returns:
            None

        Raises:
            ModuleInitFailure: Raised when one of the components isn't correct.

        '''

        # Validate template functions
        for n, f in self.config.template_functions.items():
            if not isinstance(f, TemplateFunction):
                raise ModuleInitFailure("Template function '%s' does not base TemplateFunction." % (n))

        # Validate module functions
        for n, f in self.config.module_functions.items():
            if not isinstance(f, ModuleFunction):
                raise ModuleInitFailure("Module function '%s' does not base ModuleFunction." % (n))

        if self.MODULE_TYPE == ModuleType.OUTPUT:
            if "payload" not in self.kwargs.keys():
                raise ModuleInitFailure("An 'output' module should always have a 'payload' parameter. This is a programming error.")
            if "selection" not in self.kwargs.keys():
                raise ModuleInitFailure("An 'output' module should always have a 'selection' parameter. This is a programming error.")
