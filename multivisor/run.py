from eventlet.wsgi import ALREADY_HANDLED
from repoze.bfg.configuration import Configurator
from multivisor.amqp import EXCHANGE
from multivisor.models import Root
from multivisor.server.websocket import WebSocketView
from webob.response import Response
from werkzeug import DebuggedApplication
from werkzeug.debug import DebuggedApplication

import eventlet
import random

from pprint import pformat
count = 0

class EchoWebsocket(WebSocketView):

    def handler(self, ws):

        while True:
            m = ws.wait()
#            import ipdb; ipdb.set_trace()
            if m is None:
                break
            ws.send('%s says %s (env %s)' % (ws.origin, m, pformat(ws.environ)))

class PlotWebsocket(WebSocketView):

    def handler(self, ws):
        for i in xrange(10000):
            ws.send("0 %s %s\n" % (i, random.random()))
            eventlet.sleep(0.1)

def ws_view(request):
    global count
    eventlet.sleep(1)
    count += 1
    return Response('view %s' % count)


def app(global_config, **settings):
    """ This function returns a WSGI application.
    
    It is usually called by the PasteDeploy framework during 
    ``paster serve``.
    """
    zcml_file = settings.get('configure_zcml', 'configure.zcml')
    root = Root(settings.get('amqp_host', 'localhost'),
                settings.get('amqp_exchange', EXCHANGE))
    config = Configurator(root_factory=lambda request: root, settings=settings)
    config.begin()
    config.load_zcml(zcml_file)
    config.end()
    if settings.get('debug', None):
        return DebuggedApplication(config.make_wsgi_app(), True)
    else:
        return config.make_wsgi_app()
