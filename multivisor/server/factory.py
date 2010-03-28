import eventlet
from eventlet import wsgi
from multivisor.server.websocket import dispatch


def server_factory(global_conf, host, port):
    port = int(port)
    def serve(app):
        listener = eventlet.listen((host, port))
        wsgi.server(listener, app)
    return serve

def websocket_app_factory(global_conf, **settings):
    return dispatch
