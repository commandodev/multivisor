from eventlet import Queue, spawn_n
from json import loads
from webob.response import Response
from zope.interface import implements
import os, sys
import eventlet

from multivisor.amqp import connect_to_amqp, EXCHANGE, create_routing_key, deserialize_routing_key
from multivisor.interfaces import *

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
        self.router.setdefault(host, Host()).update(body)


class Host(TreeNode):
    """Represents a machine running supervisor"""

    def update(self, msg):
        pass

class SupervisorInstance(object):
    implements(ISupervisorInstance)


class Process(object):
    implements(ISupervisorProcess)
