from repoze.bfg.configuration import Configurator
from multivisor.models import get_root
from webob.response import Response
from werkzeug import DebuggedApplication
from eventlet import sleep
from werkzeug.debug import DebuggedApplication

count = 0

def ws_view(request):
    global count
    sleep(1)
    count += 1
    return Response('view %s' % count)

def app(global_config, **settings):
    """ This function returns a WSGI application.
    
    It is usually called by the PasteDeploy framework during 
    ``paster serve``.
    """
    zcml_file = settings.get('configure_zcml', 'configure.zcml')
    config = Configurator(root_factory=get_root, settings=settings)
    config.begin()
    config.load_zcml(zcml_file)
    config.end()
    return DebuggedApplication(config.make_wsgi_app(), True)
