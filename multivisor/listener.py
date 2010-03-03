from eventlet import patcher
amqp = patcher.import_patched('amqplib.client_0_8')
import eventlet
import sys
import logging
from pprint import pformat

EXCHANGE='example'
HOST = 'localhost'
QNAME = 'supervisor'

def amqp_callback(msg):
    msg.channel.basic_ack(msg.delivery_tag)
    print "Got message", msg.routing_key, msg.body

def connect_to_amqp(hostname=HOST, exchange=EXCHANGE, qname=QNAME):
    conn = amqp.Connection(hostname, userid='guest', password='guest', ssl=False, insist=True)
    ch = conn.channel()
    ch.access_request('/data', active=True, read=True)
    ch.exchange_declare(exchange, 'topic', auto_delete=True, durable=False)
    qname, _, _ = ch.queue_declare(qname, auto_delete=True, durable=False)
    return ch


def amqp_events(keys=['procs.*'], qname=QNAME):
    ch = connect_to_amqp()
    for key in keys:
        ch.queue_bind(qname, EXCHANGE, key)
    ch.basic_consume(qname, callback=amqp_callback)
    while ch.callbacks:
        ch.wait()


#logging.basicConfig(filename='/tmp/listener.log', level=logging.DEBUG,
#                    format='%(name)s %(message)s')
#log = logging.getLogger('listener')

def write_stdout(s):
    sys.stdout.write(s)
    sys.stdout.flush()

def write_stderr(s):
    sys.stderr.write(s)
    sys.stderr.flush()

def supervisor_events():
    ch = connect_to_amqp()

    while 1:
        write_stdout('READY\n') # transition from ACKNOWLEDGED to READY
        line = sys.stdin.readline()  # read header line from stdin
        write_stderr(line) # print it out to stderr
        headers = dict([ x.split(':') for x in line.split() ])
        header_msg = amqp.Message(pformat(headers),
                                  content_type='text/plain', application_headers=headers)
        data = sys.stdin.read(int(headers['len'])) # read the event payload
        log_data = dict([ x.split(':') for x in data.split() ])
        write_stderr(data) # print the event payload to stderr
        data_msg = amqp.Message(pformat(log_data),
                                content_type='text/plain', application_headers=log_data)
        ch.basic_publish(header_msg, EXCHANGE, routing_key='procs.headers')
        ch.basic_publish(data_msg, EXCHANGE, routing_key='procs.data')
        write_stdout('RESULT 2\nOK') # transition from READY to ACKNOWLEDGED

if __name__ == '__main__':
    supervisor_events()
    import sys
