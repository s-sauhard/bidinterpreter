from django.http import HttpResponse
from django.conf import settings
import base64

class BasicAuthMiddleware(object):
    
    def __init__(self, get_response, **kwargs):
        self.get_response = get_response
    
    def __call__(self, request):
        if 'HTTP_AUTHORIZATION' not in request.META:
            return self.unauthed()
        else:
            authentication = request.META['HTTP_AUTHORIZATION']
            (auth_method, auth) = authentication.split(' ', 1)
            if 'basic' != auth_method.lower():
                return self._unauthed()
            auth = base64.b64decode(auth.strip()).decode('utf-8')
            username, password = auth.split(':', 1)
            if (
                username == settings.BASICAUTH_USERNAME and
                password == settings.BASICAUTH_PASSWORD
            ):
                return self.get_response(request)

            return self.unauthed()

    def unauthed(self):
        response = HttpResponse("""<html><title>Auth required</title><body>
                                <h1>Authorization Required</h1></body></html>""", content_type="text/html")
        response['WWW-Authenticate'] = 'Basic realm="Development"'
        response.status_code = 401
        return response
    
    def process_request(self,request):
        if not request.META.has_key('HTTP_AUTHORIZATION'):
            
            return self.unauthed()
        else:
            authentication = request.META['HTTP_AUTHORIZATION']
            (authmeth, auth) = authentication.split(' ',1)
            if 'basic' != authmeth.lower():
                return self.unauthed()
            auth = base64.decode(auth.strip())
            username, password = auth.split(':',1)
            if username == settings.BASICAUTH_USERNAME and password == settings.BASICAUTH_PASSWORD:
                return None
            
            return self.unauthed()