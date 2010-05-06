from zope.interface import Interface, Attribute
from repoze.bfg.interfaces import IRequest

class ITreeNode(Interface):
    """Base class for objects that are part of the tree

    Defines methods for interacting with websockets
    """

    router = Attribute("A dict of child objects (proxied by __getitem__")

    def send(message):
        """Send a message to all attached WebSockets"""

    def add_ws_listener(websocket):
        """Adds websocket to the set of attached WebSockets"""

    def remove_ws_listener(websocket):
        """Discards websocket from the set of attached WebSockets"""

class IHost(ITreeNode):
    """A host running supervisor"""

class ISupervisorInstance(ITreeNode):
    """An instance of supervisor running on a host"""

    name = Attribute("""Name of the supervisord instance (set in
                        supervisor.config""")
    host_name = Attribute("""Host that this instance is running on""")


class ISupervisorProcess(ITreeNode):
    """A process managed by a :class:`ISupervisorInstance`"""

    supervisor = Attribute("""The :class:`ISupervisorInstance` this process is
                              running in""")
    state = Attribute("""The current state of this process""")

class IWebsocketUpgradeRequest(IRequest):
    """An http request to upgrade to websocket"""
