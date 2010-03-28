from webob.response import Response
from zope.interface import implements

from multivisor.interfaces import *

class Root(object):

    def __init__(self):
        pass

    def __getitem__(self, key):
        return Response('test')


class SupervisorInstance(object):
    implements(ISupervisorInstance)


class Process(object):
    implements(ISupervisorProcess)



root = Root()

def get_root(request):
    return root
