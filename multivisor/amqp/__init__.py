from collections import namedtuple
from eventlet import patcher
amqplib = patcher.import_patched('amqplib.client_0_8')

EXCHANGE='processes'
HOST = 'localhost'

RoutingKey = namedtuple('RoutingKey', 'host supervisor_id process_name event_type')

def create_routing_key(host='*', supervisor_id='*', process_name='*', event_type='*'):
    return "%s.%s.%s.%s" % (host.replace('.','|'), supervisor_id, process_name, event_type)

def deserialize_routing_key(routing_key):
    replace_star = lambda p: None if p == '*' else p
    parts = [replace_star(p) for p in routing_key.split('.')]
    host = parts[0]
    if host:
       parts[0] = host.replace('|', '.')
    return RoutingKey(*parts)


def connect_to_amqp(hostname=HOST, exchange=EXCHANGE, durable=True, auto_delete=False):
    conn = amqplib.Connection(hostname, userid='guest', password='guest', ssl=False, insist=True)
    ch = conn.channel()
    ch.access_request('/data', active=True, read=True)
    ch.exchange_declare(exchange, 'topic', durable=durable, auto_delete=auto_delete)
    return ch