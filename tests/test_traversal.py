from nose.tools import *
from nose.exc import SkipTest
from unittest import TestCase
from eventlet.green import socket
from eventlet import greenthread, debug, hubs, Timeout, spawn_n, tpool
from multivisor.amqp import connect_to_amqp, create_routing_key, deserialize_routing_key
from multivisor.models import *
from multivisor.listener import EventParser
from multivisor.server.websocket import WebSocket
import eventlet
import mock

AMQP_HOST = 'localhost'
TEST_EXCHANGE = 'test'
TEST_KWARGS = dict(durable=True, auto_delete=False)

class MessageSender(EventParser):

    def _get_rpc(self, env=None):
        rpc = mock.Mock()
        rpc.supervisor.getIdentification.return_value = 'supervisor'
        return rpc

class TestIsTakingTooLong(Exception):
    """ Custom exception class to be raised when a test's runtime exceeds a limit. """
    pass

class TestTraversal(TestCase):

    TEST_TIMEOUT = 1

    def setUp(self):
        try:
            self.sender = MessageSender(AMQP_HOST, TEST_EXCHANGE, **TEST_KWARGS)
            self.root = Root(AMQP_HOST, TEST_EXCHANGE, **TEST_KWARGS)
        except socket.error:
            raise SkipTest('amqp not available')
        self.timer = Timeout(self.TEST_TIMEOUT,
                             TestIsTakingTooLong(self.TEST_TIMEOUT))


    def tearDown(self):
        self.timer.cancel()
        greenthread.kill(self.root.listener)
        eventlet.sleep(0)
        try:
            hub = hubs.get_hub()
            num_readers = len(hub.get_readers())
            num_writers = len(hub.get_writers())
            assert num_readers == num_writers == 0
        except AssertionError, e:
            print "ERROR: Hub not empty"
            print debug.format_hub_timers()
            print debug.format_hub_listeners()

    def reset_timeout(self, new_timeout):
        """Changes the timeout duration; only has effect during one test case"""
        self.timer.cancel()
        self.timer = Timeout(new_timeout,
                             TestIsTakingTooLong(new_timeout))

    def send_msg(self, body, rk):
        eventlet.sleep(0.1)
        self.sender.dispatch_message(body, rk)
        eventlet.sleep(0.1)


    def test_root_sets_up_new_hosts(self):
        rk = create_routing_key('new_host', 'supervisor', 'process', 'TICK')
        self.send_msg({'body': 'test'}, rk)
        ok_('new_host' in self.root.router)
        host = self.root['new_host']
        # send the same message shouldn't recreate the host
        self.send_msg({'body': 'test'}, rk)
        ok_(host is self.root['new_host'])


class TestTreeNode(TestCase):

    def setUp(self):
        self.tn = TreeNode()
        self.mock_socket = s = mock.Mock()
        self.environ = env = dict(HTTP_ORIGIN='http://localhost', HTTP_WEBSOCKET_PROTOCOL='ws',
                                  PATH_INFO='test')

        self.test_ws = WebSocket(s, env)

    def test_tree_node_has_listeners(self):
        eq_(self.tn.ws_listeners, set())

    def test_tree_node_router(self):
        self.tn.router['a_key'] = 'something'
        eq_(self.tn['a_key'], 'something')
        assert_raises(KeyError, self.tn.__getitem__, 'test')

    def test_tree_node_add_listeners(self):
        ws = self.test_ws
        OTHER_WS = WebSocket(self.mock_socket, self.environ)
        tn = self.tn
        eq_(tn.ws_listeners, set())
        tn.add_ws_listener(ws)
        eq_(tn.ws_listeners, set([ws]))
        tn.add_ws_listener(ws)
        eq_(tn.ws_listeners, set([ws]))
        tn.remove_ws_listener(OTHER_WS)
        eq_(tn.ws_listeners, set([ws]))
        tn.remove_ws_listener(ws)
        eq_(tn.ws_listeners, set())

    def test_send_to_ws(self):
        tn = self.tn
        ws = self.test_ws
        tn.add_ws_listener(ws)
        tn.send('hello')
        ok_(ws.socket.sendall.called_with("\x00hello\xFF"))




