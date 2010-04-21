from collections import deque
from eventlet import Queue, spawn_n
from json import loads, dumps
from repoze.bfg.traversal import model_path
from webob.response import Response
from zope.interface import implements
import os, sys, logging, pprint
import eventlet

from multivisor.amqp import connect_to_amqp, EXCHANGE, create_routing_key, deserialize_routing_key
from multivisor.interfaces import *

logger = logging.getLogger('mv.models')

class TreeNode(object):

    def __new__(cls, *args, **kwargs):
        new_inst = super(TreeNode, cls).__new__(cls)
        new_inst.ws_listeners = set()
        return new_inst

    @property
    def router(self):
        if not hasattr(self, '_router'):
            self._router = dict()
        return self._router

    @property
    def path(self):
        return model_path(self)

    @property
    def ws_path(self):
        return self.path.replace('http', 'ws')

    @property
    def id(self):
        return model_path(self).strip('/').replace('/', '-').replace('.', '_')

    def __getitem__(self, key):
        return self.router[key]

    def add_ws_listener(self, ws):
        """Adds a :class:`mulitvisor.server.websocket.Websocket` the the set of listeners"""
        self.ws_listeners.add(ws)

    def remove_ws_listener(self, ws):
        """Removes ws from the set of listeners"""
        self.ws_listeners.discard(ws)

    def send(self, message):
        for ws in self.ws_listeners:
            ws.send(message)


class Root(TreeNode):

    __parent__ = None
    __name__ = ''
    QNAME = 'root%s' % os.getpid()

    def __init__(self, amqp_host, amqp_exchange=EXCHANGE, **kwargs):
        self.amqp_host = amqp_host
        self.amqp_exchange = amqp_exchange
        self.channel = connect_to_amqp(amqp_host, amqp_exchange, **kwargs)
        self.message_queue = Queue()
        self.listener = spawn_n(self.subscribe)

    def subscribe(self):
        chan = self.channel
        qname=  self.QNAME
        qname, _, _ = chan.queue_declare(qname, auto_delete=True, durable=False)
        rk = create_routing_key(event_type='TICK')
        chan.queue_bind(qname, self.amqp_exchange, rk)
        chan.basic_consume(qname, callback=self.handle_message)
        while chan.callbacks:
            try:
                chan.wait()
            except (KeyboardInterrupt, SystemExit):
                sys.exit()

    def handle_message(self, msg):
        msg.channel.basic_ack(msg.delivery_tag)
        body = loads(msg.body)
        self.update(msg.routing_key, body)

    def update(self, routing_key, body):
        routing_key = deserialize_routing_key(routing_key)
        host = routing_key.host
        self.router.setdefault(host, Host(self, host)).update(routing_key, body)

    def all_processes(self):
        procs = []
        for host in self.router.values():
            procs.extend(host.all_processes())
        return procs



class SubTreeNode(TreeNode):
    """SubTreeNodes are initialized with information about their parents"""

    def __init__(self, parent, name):
        self.__parent__ = parent
        self.__name__ = self.name = name

    def _child_class(self):
        return None

    @property
    def child_class(self):
        return self._child_class()

    def _rk_attr(self):
        return None

    @property
    def routing_key_attribute(self):
        return self._rk_attr()

    def get_handler_for_event_type(self, event_type):
        """Get a callable to handle this type of message"""
        return None

    def update(self, routing_key, message):

        if self.child_class and self.routing_key_attribute:
            child_id = getattr(routing_key, self.routing_key_attribute)
            self.router.setdefault(child_id,
                                   self.child_class(self, child_id))\
                                   .update(routing_key, message)
        event_handler = self.get_handler_for_event_type(routing_key.event_type)
        if event_handler:
            event_handler(routing_key, message)
            
class Host(SubTreeNode):
    """Represents a machine running supervisor"""

    def _child_class(self):
        return SupervisorInstance

    def _rk_attr(self):
        return 'supervisor_id'

    def all_processes(self):
        procs = []
        for sv in self.router.values():
            procs.extend(sv.router.values())
        return procs


class SupervisorInstance(SubTreeNode):
    implements(ISupervisorInstance)

    def _child_class(self):
        return Process

    def _rk_attr(self):
        return 'process_name'

"""
Got message  mac|local.supervisor.mv-listener.TICK
{u'description': u'pid 11083, uptime 0:00:01',
 u'exitstatus': 0,
 u'group': u'mv-listener',
 u'logfile': u'/tmp/mv-listener-stdout---supervisor-DFSwcr.log',
 u'name': u'mv-listener',
 u'now': 1271310522,
 u'pid': 11083,
 u'process_info': {u'cpu_percent': 75.581395348837205,
                   u'mem_percent': 0.30269622802734375,
                   u'mem_resident': 13000704,
                   u'mem_virtual': 2515353600},
 u'spawnerr': u'',
 u'start': 1271310521,
 u'state': 20,
 u'statename': u'RUNNING',
 u'stderr_logfile': u'/tmp/mv.stdout',
 u'stdout_logfile': u'/tmp/mv-listener-stdout---supervisor-DFSwcr.log',
 u'stop': 0}
"""

class Process(SubTreeNode):
    implements(ISupervisorProcess)

    def __init__(self, parent, name):
        super(Process, self).__init__(parent, name)
        self.mem_info = deque([], 1000)
        self.proc_info = deque([], 1000)
        self.state = None
        self.last_tick_time = None
        self.start_time = None

    @property
    def server(self):
        # TODO: This assumes the current structure, refactor
        return self.__parent__.__parent__

    def get_handler_for_event_type(self, event_type):
        if event_type.startswith('TICK'):
            return self.handle_tick

    def handle_tick(self, routing_key, message):

        try:
            timestamp = message['now']
            self.start_time = message['start']
            self.last_tick_time = message['now']
            self.state = message['statename']
            process_info = message['process_info']
            self.proc_info.append(dict(timestamp=timestamp,
                                       cpu=process_info['cpu_percent']))
            self.mem_info.append(dict(timestamp=timestamp,
                                      mem_percent=process_info['mem_percent']))
            self.send(dumps(message))
        except KeyError, e:
            logger.error("%s: Malformed message %s" % (e, pprint.pformat(message)))


