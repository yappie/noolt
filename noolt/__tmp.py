import cherrypy.wsgiserver
import time
import urllib
from thread import start_new_thread

def app(a,b):
    return

while 1:
    serv = cherrypy.wsgiserver.CherryPyWSGIServer(('0.0.0.0', 2112), app, numthreads = 4)
    start_new_thread(serv.start, ())
    time.sleep(.01)
    urllib.urlopen('http://127.0.0.1:2112').read()
    serv.stop()
    time.sleep(.01)
    print "loop"


print serv.ready
