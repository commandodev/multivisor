from eventlet import Queue, spawn_n
from json import loads
from webob.response import Response
from zope.interface import implements
import os, sys

from multivisor.amqp import connect_to_amqp, EXCHANGE, create_routing_key, deserialize_routing_key
from multivisor.interfaces import *

class TreeNode(object):

    @property
    def router(self):
        if not hasattr(self, '_router'):
            self._router = dict()
        return self._router

    def __getitem__(self, key):
        return self.router[key]


class Root(TreeNode):

    QNAME = 'root%s' % os.getpid()

    def __init__(self, amqp_host, amqp_exchange=EXCHANGE):
        self.channel = connect_to_amqp(amqp_host, amqp_exchange)
        self.message_queue = Queue()
        spawn_n(self._listen_for_messages)

    def _listen_for_messages(self):
        chan = self.channel
        qname=  self.QNAME
        qname, _, _ = chan.queue_declare(qname, auto_delete=True, durable=False)
        chan.queue_bind(qname, EXCHANGE, create_routing_key(event_type='TICK'))
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
