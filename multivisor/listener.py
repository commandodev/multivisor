from eventlet import patcher
import os
childutils = patcher.import_patched('supervisor.childutils')
from multivisor.amqp import connect_to_amqp, EXCHANGE, amqplib, create_routing_key
from json import dumps
from pprint import pformat
import baker
import psutil
import logging
import os
import socket
import sys

logging.basicConfig(filename='/tmp/listener.log', level=logging.INFO)
HOST = socket.gethostname()


class WrongEventType(TypeError):
    """An exception for an :class:`EventParser` trying to process the wrong supervisor event"""

class EventParser(object):
    """Base class for handling supervisor events"""

    #: The event type being listened to
    EVENT_NAME = 'EVENT'

    PROTOCOL = childutils.EventListenerProtocol()
    #: The ``delivery_mode`` of messages (1 == Non persistent)
    DELIVERY_MODE = 1
    #: Message content_type
    CONTENT_TYPE = 'application/json'
    log = logging.getLogger('listener')

    def __init__(self, amqp_host, exchange, stdin=sys.stdin, stdout=sys.stdout, **kwargs):
        self.amqp_host = amqp_host
        self.exchange = exchange
        self.stdin = stdin
        self.stdout = stdout
        self.rpc = self._get_rpc()
        self.supervisor_id = self.rpc.supervisor.getIdentification()
        self.channel = connect_to_amqp(amqp_host, exchange, **kwargs)

    def _get_rpc(self, env=os.environ):
        return childutils.getRPCInterface(env)

    def ready(self):
        self.PROTOCOL.ready(self.stdout)

    def ok(self):
        self.PROTOCOL.ok(self.stdout)

    def wait(self):
        headers, payload =  self.PROTOCOL.wait(self.stdin, self.stdout)
        return headers, childutils.get_headers(payload)

    def process_event(self, headers, payload):
        """Add any additional information to payload

        :param payload: The body of the parsed supervisor message
        :type payload: dict
        """
        pass

    def construct_routing_key(self, process_name):
        """Build a routing key to send messages to

        :param process_name: The name of the process
        :returns: 'hostname.supervisor_id.process_name.:attr:`event_name <EVENT_NAME>`'
        """
        return create_routing_key(HOST, self.supervisor_id, process_name, self.EVENT_NAME)

    def dispatch_message(self, routing_key, message_body, content_type=None):
        if not content_type:
            content_type = self.CONTENT_TYPE
        msg = amqplib.Message(dumps(message_body), content_type=content_type)
        self.channel.basic_publish(msg, self.exchange, routing_key)

    def run(self, test=False):
        self.log.debug('run')
        while 1:
            sys.stderr.write('tick')
            headers, payload = self.wait()
            try:
                self.process_event(headers, payload)
            except:
                self.log.exception('oops')
            finally:
                sys.stderr.flush()
                self.ok()
                if test:
                    break


class Tick5Parser(EventParser):

    EVENT_NAME = 'TICK'
    def __init__(self, *args, **kwargs):
        super(Tick5Parser, self).__init__(*args, **kwargs)
        self.procs = {}
        self.leak = []
        self.count = 0

    def process_event(self, headers, payload):
        if self.count % 5 == 0:
            self.leak = []
        self.leak.append(range(10000))
        all_procs = self.rpc.supervisor.getAllProcessInfo()
        self.log.info(all_procs)
        for proc in all_procs:
            process_name = proc['name']
            pid = int(proc['pid'])
            proc['process_info'] = self.get_process_info(pid)
            routing_key = self.construct_routing_key(process_name)
            self.dispatch_message(routing_key, proc)

    def get_process_info(self, pid):
#        ps = self.procs.setdefault(pid, psutil.Process(pid))
        ps = psutil.Process(pid)
        try:
            rss, vms = ps.get_memory_info()
        except:
            rss = vms = None
        return dict(cpu_percent=ps.get_cpu_percent(),
                    mem_percent=ps.get_memory_percent(),
                    mem_resident=rss,
                    mem_virtual=vms)




@baker.command
def tick(host):
    log = logging.getLogger('runner')
    log.debug('command')
    try:
        parser = Tick5Parser(host, EXCHANGE)
#        import pdb; pdb.set_trace()
        parser.run()
    except Exception, e:
        log.exception(e)

def run():
    baker.run()

if __name__ == '__main__':
    baker.run()
    import sys
