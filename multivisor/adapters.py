from zope import interface
from multivisor.interfaces import IWebsocketUpgradeRequest

def check_for_websocket(new_request_event):
    """Attaches the appropriate request interface to websocket requests"""
#    from nose.tools import set_trace; set_trace()
    request = new_request_event.request
    if 'Upgrade' in request.headers:
        interface.alsoProvides(request, IWebsocketUpgradeRequest)

