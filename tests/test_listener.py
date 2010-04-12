from multivisor.listener import Tick5Parser
from nose.tools import set_trace, eq_
from unittest import TestCase
from StringIO import StringIO
from mock import patch, patch_object, Mock, sentinel
import os
import socket

class _TestTick5(Tick5Parser):

    RPC_MOCK = Mock()

    def _get_rpc(self, env=os.environ):
        return self.RPC_MOCK

_TestTick5.RPC_MOCK.supervisor.getIdentification.return_value = 'supervisor'
HOSTNAME = socket.gethostname().replace('.', '|')

class TestTick5Parser(TestCase):

    @patch('multivisor.amqp.amqplib.Connection')
    def setUp(self, MockAQMP):
        os.environ['SUPERVISOR_SERVER_URL'] = 'test'
        self.tick5 = _TestTick5('localhost', 'test', StringIO(), StringIO())
        self.tick5.channel = Mock()

    def test_ready(self):
        self.tick5.stdin.write('eventname:TICK5 len:5\na:one')
        self.tick5.stdin.seek(0)
        headers, payload = self.tick5.wait()
#        self.tick5.channel.basic_publish.assert_called_with(10)
        v = self.tick5.stdout.getvalue()
        self.assertEqual({'a': 'one'}, payload)
        self.assertEqual(v, 'READY\n')

    @patch_object(_TestTick5, 'get_process_info')
    @patch('multivisor.amqp.amqplib.Message')
    def test_run(self, mocked_message, mocked_process):
        mocked_process.return_value = 'MOCKED'
        self.tick5.stdin.write('eventname:TICK5 len:5\na:one')
        self.tick5.stdin.seek(0)
        all_procs = [dict(name='proc1', pid='111', val='val1'), dict(name='proc2', pid='222', val='val2')]
        self.tick5.RPC_MOCK.supervisor.getAllProcessInfo.return_value = all_procs
        self.tick5.run(test=True)
        # Mocked ampqlib.Message should have been called twice:
        call_args_list = [ca[0][0] for ca in mocked_message.call_args_list]


        eq_(len(call_args_list), 2)
        eq_(call_args_list[0], '{"process_info": "MOCKED", "pid": "111", "name": "proc1", "val": "val1"}')
        eq_(call_args_list[1], '{"process_info": "MOCKED", "pid": "222", "name": "proc2", "val": "val2"}')

        # basic_publish has also been called twice
        call_args_list = [ca[0] for ca in self.tick5.channel.basic_publish.call_args_list]
        eq_(call_args_list[0], (mocked_message.return_value, 'test', '%s.supervisor.proc1.TICK' % HOSTNAME))
        eq_(call_args_list[1], (mocked_message.return_value, 'test', '%s.supervisor.proc2.TICK' % HOSTNAME))



