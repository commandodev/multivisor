from multivisor.server.websocket import WebSocketView
import eventlet
from json import dumps
from jinja2 import Markup


def root_view(request):
    context = request.context
    running = []
    down = []
    for i, s in enumerate(context.servers):
        num_running = len(s.running_processes)
        num_total = s.num_processes
        num_down = num_total - num_running
#        if not num_down:
#            num_down = None
        running.append([i + 1, num_running])#, s.name])
        down.append([i + 1, num_down])#, s.name])
        
    running = Markup(dumps(running))
    down = Markup(dumps(down))
    return dict(processes=context.all_processes(), root=context, title='All processes', running=running, down=down)

def ws_entry(request):
    return dict(echo='/echo', data='/data',root=request.context.router)

def host_view(request):
    context = request.context
    return dict(context=context)

class HostWebsocket(WebSocketView):

    def handler(self, ws):
        self.request.context.add_ws_listener(ws)
        while True:
            m = ws.wait()
            eventlet.sleep(0.1)
