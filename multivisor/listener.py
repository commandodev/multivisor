from eventlet import patcher
import os
childutils = patcher.import_patched('supervisor.childutils')
from multivisor.amqp import connect_to_amqp, EXCHANGE, amqplib
from json import dumps
from pprint import pformat
import logging
import os
import sys

logging.basicConfig(filename='/tmp/listener.log', level=logging.INFO)

class WrongEventType(TypeError):
    """An exception for an :class:`EventParser` trying to process the wrong supervisor event"""

class EventParser(object):
    """Base class for handling supervisor events"""

    PROTOCOL = childutils.EventListenerProtocol()
    #: The ``delivery_mode`` of messages (1 == Non persistent)
    DELIVERY_MODE = 1
    #: Message content_type
    CONTENT_TYPE = 'application/json'
    log = logging.getLogger('listener')

    def __init__(self, amqp_host, exchange, routing_key, stdin=sys.stdin, stdout=sys.stdout):
        self.amqp_host = amqp_host
        self.exchange = exchange
        self.routing_key = routing_key
        self.stdin = stdin
        self.stdout = stdout
        self.rpc = self._get_rpc()
        self.channel = connect_to_amqp(amqp_host, exchange)

    def _get_rpc(self, env=os.environ):
        return childutils.getRPCInterface(env)

    def ready(self):
        self.PROTOCOL.ready(self.stdout)

    def ok(self):
        self.PROTOCOL.ok(self.stdout)

    def wait(self):
        headers, payload =  self.PROTOCOL.wait(self.stdin, self.stdout)
        return headers, childutils.get_headers(payload)

    def augment_payload(self, headers, payload):
        """Add any additional information to payload

        :param payload: The body of the parsed supervisor message
        :type payload: dict
        """
        pass

    def dispatch_message(self, message_body, content_type=None):
        if not content_type:
            content_type = self.CONTENT_TYPE
        msg = amqplib.Message(dumps(message_body), content_type=content_type)
        self.channel.basic_publish(msg, self.exchange, self.routing_key)

    def run(self, test=False):
        self.log.debug('run')
        while 1:
            sys.stderr.write('tick')
            headers, payload = self.wait()
            sys.stderr.write('headers: %s payload: %s' % (headers, payload))
            self.augment_payload(headers, payload)
            sys.stderr.write('augmented: %s' % payload)
            try:
                self.dispatch_message(payload)
            except:
                self.log.exception()
            sys.stderr.flush()
            self.ok()
            if test:
                break


class Tick5Parser(EventParser):

    def augment_payload(self, headers, payload):
        super(Tick5Parser, self).augment_payload(headers, payload)
        all_procs = self.rpc.supervisor.getAllProcessInfo()
        self.log.info(all_procs)
        update_dict = {}
        for proc in all_procs:
            process_name = proc.pop('name')
            update_dict[process_name] = proc
        payload.update(update_dict)







def supervisor_events():
    log = logging.getLogger('runner')
    log.debug('command')
    try:
        parser = Tick5Parser('localhost', EXCHANGE, 'procs.tick')
#        import pdb; pdb.set_trace()
        parser.run()
    except Exception, e:
        log.exception(e)

if __name__ == '__main__':
    supervisor_events()
    import sys
