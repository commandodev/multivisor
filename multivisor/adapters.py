#from zope import component
from zope import interface
from repoze.bfg.interfaces import INewRequest
from interfaces import IWebsocketRequest

#@component.adapter(INewRequest)
def check_for_websocket(new_request_event):
#    import ipdb; ipdb.set_trace()
    req = new_request_event.request
    if req.scheme.startswith('ws'):
        interface.alsoProvides(req, IWebsocketRequest)

