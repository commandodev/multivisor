from multivisor.listener import Tick5Parser
from nose.tools import set_trace, eq_
from unittest import TestCase
from StringIO import StringIO
from mock import patch, Mock
import os

class _TestTick5(Tick5Parser):

    def _get_rpc(self, env=os.environ):
        return Mock()

class TestTick5Parser(TestCase):

    @patch('multivisor.amqp.amqplib.Connection')
    def setUp(self, MockAQMP):
        os.environ['SUPERVISOR_SERVER_URL'] = 'test'
        self.tick5 = _TestTick5('localhost', 'test', 'test', StringIO(), StringIO())
        self.tick5.channel = Mock()

    def test_ready(self):
        self.tick5.stdin.write('eventname:TICK5 len:5\na:one')
        self.tick5.stdin.seek(0)
        headers, payload = self.tick5.wait()
#        self.tick5.channel.basic_publish.assert_called_with(10)
        v = self.tick5.stdout.getvalue()
        self.assertEqual({'a': 'one'}, payload)
        self.assertEqual(v, 'READY\n')

    @patch('multivisor.amqp.amqplib.Message')
    def test_run(self, mocked_message):
        self.tick5.stdin.write('eventname:TICK5 len:5\na:one')
        self.tick5.stdin.seek(0)
        self.tick5.run(test=True)
        mocked_message.assert_called_with('{"a": "one"}', content_type='application/json')
        self.tick5.channel.basic_publish.assert_called_with(mocked_message.return_value, 'test', 'test')



