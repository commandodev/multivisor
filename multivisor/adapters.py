#from zope import component
from zope import interface
from repoze.bfg.interfaces import INewRequest
from interfaces import IWebsocketUpgradeRequest


def check_for_websocket(new_request_event):
    """Attaches the appropriate request interface to websocket requests"""
#    from nose.tools import set_trace; set_trace()
    req = new_request_event.request
    if 'Upgrade' in req.headers:
        interface.alsoProvides(req, IWebsocketUpgradeRequest)

