from nose.tools import ok_, set_trace
from repoze.bfg.events import NewRequest
from repoze.bfg.interfaces import IRequest
from repoze.bfg.configuration import Configurator
from repoze.bfg.threadlocal import get_current_request, get_current_registry
from repoze.bfg import testing
from zope.event import notify
from zope.interface import implements
from unittest import TestCase

from multivisor.interfaces import IWebsocketRequest
from multivisor.models import get_root

class _TestReq(object):
    implements(IRequest)

    def __init__(self, environ, scheme):
        self.environ = environ
        self.scheme = scheme


class TestWebsocket(TestCase):

    def setUp(self):
        import multivisor
        self.config = testing.setUp()
        self.config.begin()
        self.config.load_zcml('multivisor:configure.zcml')
        self.config.end()

    def tearDown(self):
        testing.tearDown()


    def test_ws_scheme_attaches_iwebsocket_interface(self):
        request = _TestReq({}, 'ws')
        self.config.registry.notify(NewRequest(request))
        ok_(IWebsocketRequest.providedBy(request))

    def test_wss_scheme_attaches_iwebsocket_interface(self):
        request = request=_TestReq({}, 'wss')
        self.config.registry.notify(NewRequest(request))
        ok_(IWebsocketRequest.providedBy(request))

    def test_http_scheme_attaches_iwebsocket_interface(self):
        request = _TestReq({}, 'http')
        self.config.registry.notify(NewRequest(request))
        ok_(not IWebsocketRequest.providedBy(request))

