from nose.tools import ok_, set_trace
from repoze.bfg.events import NewRequest
from repoze.bfg.interfaces import IRequest
from repoze.bfg.configuration import Configurator
from repoze.bfg.threadlocal import get_current_request, get_current_registry
from repoze.bfg import testing
from zope.event import notify
from zope.interface import implements
from unittest import TestCase

from multivisor.interfaces import IWebsocketUpgradeRequest
from multivisor.models import get_root

class _TestReq(object):
    implements(IRequest)

    headers = dict()

    def __init__(self, environ, scheme):
        self.environ = environ
        self.scheme = scheme


class TestWebsocket(TestCase):

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


