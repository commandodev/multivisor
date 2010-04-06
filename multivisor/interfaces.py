from zope.interface import Interface, Attribute
from repoze.bfg.interfaces import IRequest

class ISupervisorInstance(Interface):
    """An instance of supervisor running on a host"""

    name = Attribute("""Name of the supervisord instance (set in supervisor.config""")
    host_name = Attribute("""Host that this instance is running on""")

    processes = Attribute("""Dict of process name: :class:`ISupervisorProcess`""")


class ISupervisorProcess(Interface):
    """A process managed by a :class:`ISupervisorInstance`"""

    supervisor = Attribute("""The class:`ISupervisorInstance` this process is running in""")
    state = Attribute("""The current state of this process""")

class IWebsocketUpgradeRequest(IRequest):
    """An http request to upgrade to websocket"""
