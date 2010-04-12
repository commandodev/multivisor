from nose.tools import *
from nose.exc import SkipTest
from unittest import TestCase
from eventlet.green import socket
from eventlet import greenthread, debug, hubs, Timeout, spawn_n, tpool
from multivisor.amqp import connect_to_amqp, create_routing_key, deserialize_routing_key
from multivisor.models import *
from multivisor.listener import EventParser
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
        except socket.error:
            raise SkipTest('amqp not available')
        self.timer = Timeout(self.TEST_TIMEOUT,
                             TestIsTakingTooLong(self.TEST_TIMEOUT))
        #eventlet.sleep(0.5)

    def tearDown(self):
        self.timer.cancel()
        #greenthread.kill(self.root.listener)
        eventlet.sleep(0)
        try:
            hub = hubs.get_hub()
            num_readers = len(hub.get_readers())
            num_writers = len(hub.get_writers())
            assert num_readers == num_writers == 0
        except AssertionError, e:
#            set_trace()
            print "ERROR: Hub not empty"
            print debug.format_hub_timers()
            print debug.format_hub_listeners()

        eventlet.sleep(0)

    def reset_timeout(self, new_timeout):
        """Changes the timeout duration; only has effect during one test case"""
        self.timer.cancel()
        self.timer = Timeout(new_timeout,
                             TestIsTakingTooLong(new_timeout))

    def test_root_sets_up_new_hosts(self):
        rk = create_routing_key('new_host', 'supervisor', 'process', 'TICK')
        root = Root(AMQP_HOST, TEST_EXCHANGE, **TEST_KWARGS)
        eventlet.sleep(0.1)
        self.sender.dispatch_message({'body': 'test'}, rk)
        eventlet.sleep(0.1)
        greenthread.kill(root.listener)
        ok_('new_host' in root.router)


    def test_2(self):
        eq_(1,1)

@raises(KeyError)
def test_tree_node():
    tn = TreeNode()
    tn.router['a_key'] = 'something'
    eq_(tn['a_key'], 'something')
    tn['test']
