def my_view(request):
    return {'project':'multivisor'}

def ws_entry(request):
    return dict(echo='/echo', data='/data',root=request.context.router)