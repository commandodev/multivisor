from zope.interface import Interface, Attribute
from repoze.bfg.interfaces import IRequest

class ITreeNode(Interface):

    router = Attribute("A dict of child objects (proxied by __getitem__")

    def send(message):
        """Send a message to all attached :class:`WebSockets <multivisor.server.websocket.WebSocket>`"""

    def add_ws_listener(ws):
        """Adds ws to the set of attached :class:`WebSockets <multivisor.server.websocket.WebSocket>`"""

    def remove_ws_listener(ws):
        """Discards ws from the set of attached :class:`WebSockets <multivisor.server.websocket.WebSocket>`"""

class IHost(ITreeNode):
    """A host running supervisor"""

class ISupervisorInstance(ITreeNode):
    """An instance of supervisor running on a host"""

    name = Attribute("""Name of the supervisord instance (set in supervisor.config""")
    host_name = Attribute("""Host that this instance is running on""")


class ISupervisorProcess(ITreeNode):
    """A process managed by a :class:`ISupervisorInstance`"""

    supervisor = Attribute("""The class:`ISupervisorInstance` this process is running in""")
    state = Attribute("""The current state of this process""")

class IWebsocketUpgradeRequest(IRequest):
    """An http request to upgrade to websocket"""
