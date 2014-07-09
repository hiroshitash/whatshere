from  django.http import HttpResponse
import datetime

def index(request):
    cache_expire = 60*60*24*365;
    response = HttpResponse()
    response['Pragma'] = 'public'
    response['Cache-Control'] = 'max-age=%s' % cache_expire
    
    expires_date = datetime.datetime.utcnow() + datetime.timedelta(365)
    expires_str = expires_date.strftime("%d %b %Y %H:%M:%S GMT")
    response['Expires'] = expires_str
        
    response.write('<script src="//connect.facebook.net/en_US/all.js"></script>')
    response.flush()
    return response
