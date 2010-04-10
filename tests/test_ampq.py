from nose.tools import eq_

from multivisor.amqp import *

def test_create_routing_key():
    eq_(create_routing_key(host='localhost', supervisor_id='test', process_name='test_proc', event_type='TICK'),
        'localhost.test.test_proc.TICK')
    eq_(create_routing_key(host='localhost.net', process_name='test_proc', event_type='TICK'),
        'localhost|net.*.test_proc.TICK')
    eq_(create_routing_key(), '*.*.*.*')

def test_deserialize_routing_key():
    eq_(deserialize_routing_key('*.*.*.*'), RoutingKey(*[None]*4))
    eq_(deserialize_routing_key('localhost|net.*.test_proc.TICK'),
        RoutingKey('localhost.net', None, 'test_proc', 'TICK'))
    rk = deserialize_routing_key('*.*.*.*')
    eq_(rk.host, None)
    eq_(rk.supervisor_id, None)
    eq_(rk.process_name, None)
    eq_(rk.event_type, None)

