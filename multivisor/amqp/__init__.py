from eventlet import patcher
amqplib = patcher.import_patched('amqplib.client_0_8')

EXCHANGE='processes'
HOST = 'localhost'

def connect_to_amqp(hostname=HOST, exchange=EXCHANGE):
    conn = amqplib.Connection(hostname, userid='guest', password='guest', ssl=False, insist=True)
    ch = conn.channel()
    ch.access_request('/data', active=True, read=True)
    ch.exchange_declare(exchange, 'topic', durable=True, auto_delete=False)
    return ch