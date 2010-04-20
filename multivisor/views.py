from multivisor.server.websocket import WebSocketView
import eventlet


def root_view(request):
    context = request.context
    return dict(processes=context.all_processes(), root=context, title='All processes')

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
