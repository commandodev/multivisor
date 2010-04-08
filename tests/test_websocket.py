import eventlet
from eventlet import debug, hubs, Timeout, spawn_n, greenthread, wsgi
from eventlet.green import urllib2
from nose.tools import ok_, eq_, set_trace, raises
from paste import deploy
from repoze.bfg.events import NewRequest
from repoze.bfg.interfaces import IRequest
from repoze.bfg.configuration import Configurator
from repoze.bfg.threadlocal import get_current_request, get_current_registry
from repoze.bfg import testing
from StringIO import StringIO
from zope.event import notify
from zope.interface import implements
from unittest import TestCase

from multivisor.interfaces import IWebsocketUpgradeRequest
from multivisor.server.factory import server_factory
from multivisor.models import get_root
from multivisor.server.websocket import WebSocketView

from repoze.debug.responselogger import ResponseLoggingMiddleware
from logging import getLogger




class EchoWebsocket(WebSocketView):

    def handler(self, ws):
        while True:
            m = ws.wait()
#            import ipdb; ipdb.set_trace()
            if m is None:
                break
            ws.send('%s says %s (env %s)' % (ws.origin, m, str(ws.environ)))

class PlotWebsocket(WebSocketView):

    def handler(self, ws):
        for i in xrange(10000):
            ws.send("0 %s %s\n" % (i, random.random()))
            eventlet.sleep(0.1)

serve = server_factory({}, 'localhost', 6544)

##### Borrowed from the eventlet tests package

class TestIsTakingTooLong(Exception):
    """ Custom exception class to be raised when a test's runtime exceeds a limit. """
    pass

class LimitedTestCase(TestCase):
    """ Unittest subclass that adds a timeout to all tests.  Subclasses must
    be sure to call the LimitedTestCase setUp and tearDown methods.  The default
    timeout is 1 second, change it by setting self.TEST_TIMEOUT to the desired
    quantity."""

    TEST_TIMEOUT = 4
    SERVE = server_factory({}, 'localhost', 6544)

    def setUp(self):
        import eventlet
#        self.timer = Timeout(self.TEST_TIMEOUT,
#                             TestIsTakingTooLong(self.TEST_TIMEOUT))
        config = testing.setUp()
        config.begin()
        config.load_zcml('multivisor:configure.zcml')
        config.end()
        self.config = config
        self.logfile = StringIO()
        self.killer = None
        self.spawn_server()
        eventlet.sleep(0.5)

    def reset_timeout(self, new_timeout):
        """Changes the timeout duration; only has effect during one test case"""
        self.timer.cancel()
        self.timer = eventlet.Timeout(new_timeout,
                                      TestIsTakingTooLong(new_timeout))

    def spawn_server(self, **kwargs):
        """Spawns a new wsgi server with the given arguments.
        Sets self.port to the port of the server, and self.killer is the greenlet
        running it.

        Kills any previously-running server."""
        if self.killer:
            greenthread.kill(self.killer)
            eventlet.sleep(0)
        app = self.config.make_wsgi_app()
#        middleware = ResponseLoggingMiddleware(
#               app,
#               max_bodylen=3072,
#               keep=100,
#               verbose_logger=getLogger('verbose'),
#               trace_logger=getLogger('trace'),
#              )
        new_kwargs = dict(max_size=128,
                          log=self.logfile)
        new_kwargs.update(kwargs)

        sock = eventlet.listen(('localhost', 0))

        self.port = sock.getsockname()[1]
        self.killer = eventlet.spawn_n(wsgi.server, sock, app, **new_kwargs)

    def tearDown(self):
#        self.timer.cancel()
        greenthread.kill(self.killer)
        eventlet.sleep(0)
        try:
            hub = hubs.get_hub()
            num_readers = len(hub.get_readers())
            num_writers = len(hub.get_writers())
            assert num_readers == num_writers == 0
        except AssertionError, e:
#            set_trace()
            print "ERROR: Hub not empty"
            print debug.format_hub_timers()
            print debug.format_hub_listeners()

        eventlet.sleep(0)

    @raises(urllib2.HTTPError)
    def test_incorrect_headers(self):
        try:
            urllib2.urlopen("http://localhost:%s/echo" % self.port)
        except urllib2.HTTPError, e:
            eq_(e.code, 500)
            raise

    def test_correct_upgrade_request(self):
        connect = [
                "GET /echo HTTP/1.1",
                "Upgrade: WebSocket",
                "Connection: Upgrade",
                "Host: localhost:%s" % self.port,
                "Origin: http://localhost:%s" % self.port,
                "WebSocket-Protocol: ws",
                ]
        sock = eventlet.connect(
            ('localhost', self.port))

        fd = sock.makefile('rw', close=True)
        fd.write('\r\n'.join(connect) + '\r\n\r\n')
        fd.flush()
        result = sock.recv(1024)
        fd.close()
        ## The server responds the correct Websocket handshake
        eq_(result, '\r\n'.join(['HTTP/1.1 101 Web Socket Protocol Handshake',
                                 'Upgrade: WebSocket',
                                 'Connection: Upgrade',
                                 'WebSocket-Origin: http://localhost:%s' % self.port,
                                 'WebSocket-Location: ws://localhost:%s/echo\r\n\r\n' % self.port]))



class TestWebsocketAdaptation(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.begin()
        self.config.load_zcml('multivisor:configure.zcml')
        self.config.end()

    def tearDown(self):
        testing.tearDown()

    def test_websocket_upgrade_request(self):
        request = testing.DummyRequest(headers=dict(Upgrade='Websocket'), scheme='http')
        self.config.registry.notify(NewRequest(request))
        ok_(IWebsocketUpgradeRequest.providedBy(request))


