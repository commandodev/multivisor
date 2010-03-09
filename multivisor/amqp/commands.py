import baker
from multivisor.amqp import connect_to_amqp, EXCHANGE
import sys
from json import loads
from pprint import pprint

def amqp_callback(msg):
    msg.channel.basic_ack(msg.delivery_tag)
    print "Got message ", msg.routing_key
    pprint(loads(msg.body))
    print '#'*80

@baker.command
def listen(keys, qname='procs'):
    print keys
    keys = keys.split(',')
    ch = connect_to_amqp()
    qname, _, _ = ch.queue_declare(qname, auto_delete=True, durable=False)
    for key in keys:
        ch.queue_bind(qname, EXCHANGE, key)
    ch.basic_consume(qname, callback=amqp_callback)
    while ch.callbacks:
        try:
            ch.wait()
        except (KeyboardInterrupt, SystemExit):
            sys.exit()


def main():
    baker.run()