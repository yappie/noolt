from cherrypy.wsgiserver import CherryPyWSGIServer
from thread import start_new_thread
from collections import defaultdict
import helpers
import time
import re
import socket

def to_ip(host_port_string):
    if ':' not in host_port_string:
        host_port_string += ':80'
    host, _, port = host_port_string.partition(':')
    port = int(port)
    if not re.findall(r'^\d+\.\d+\.\d+\.\d+$', host):
        host = socket.gethostbyname(host)
    
    # XXX: cached ips
    return '%s:%d' % (host, port)

def start_serv(serv):
    #with helpers.Print('start %s' % serv.bind_addr[1]):
        serv.start()

class HTTPds:
    def __init__(self):
        self.hosts = defaultdict(list)
        self.running_tests = False
        self.servs = {}

    def _stop_httpd(self, host_port):
        host_port = to_ip(host_port)
        if not self.running_tests:
            #print "Stop!", host_port
            self.servs[host_port].stop()
            del self.servs[host_port]
        
    def _start_httpd(self, host_port):
        host_port = to_ip(host_port)
        if not self.running_tests:
            if host_port not in self.servs:
                host, _, port = host_port.partition(':')
                serv = CherryPyWSGIServer((host, int(port)), self.dispatcher,
                    request_queue_size = 128,  numthreads = 4)
                start_new_thread(start_serv, (serv,))
                #while not serv.ready:
                #    time.sleep(.1)
                self.servs[host_port] = serv
                while not self.servs[host_port].ready:
                    time.sleep(.001)

    def add_host(self, added, callback):
        added = to_ip(added)
        if self.hosts[added]:
            assert self.hosts[added][0] == callback, (
                self.hosts[added][0].im_self, callback.im_self
             )
        self.hosts[added].append(callback)
        self._start_httpd(added)
    
    def remove_host(self, removed):
        removed = to_ip(removed)
        self.hosts[removed].pop()
        if len(self.hosts[removed]) == 0:
            del self.hosts[removed]
            self._stop_httpd(removed)

    def add_remove(self, callback, new_hosts, old_hosts):
        new_hosts = set(new_hosts)
        old_hosts = set(old_hosts)
        for added in new_hosts - old_hosts:
            self.add_host(added, callback)
            
        for removed in old_hosts - new_hosts:
            self.remove_host(removed)

    def dispatcher(self, e, s):
        ip = to_ip(e['HTTP_HOST'])
        try:
            if ip in self.hosts:
                return self.hosts[ip][0](e,s)
            else:
                raise Exception('Not Found')  # XXX: out info
        except:
            s('403 Error', [])
            return ['Host not found\n\n<!-- err:responder_not_found -->',]
        
def run_test():

    assert to_ip('localhost') == '127.0.0.1:80'

    dummy = lambda x,y:124
    h = HTTPds()
    h.running_tests = True
    h.add_remove(dummy, ['1.1.1.1',], [])
    assert h.hosts.keys() == ['1.1.1.1:80',]
    h.add_remove(dummy, ['2.2.2.2'], ['1.1.1.1',])
    assert h.hosts.keys() == ['2.2.2.2:80',]

    h.add_host('1.1.1.1', dummy)
    assert h.hosts.keys() == ['2.2.2.2:80','1.1.1.1:80',]
    h.remove_host('1.1.1.1')
    assert h.hosts.keys() == ['2.2.2.2:80',]

    h.add_host('localhost:80', dummy)
    assert h.hosts.keys() == ['127.0.0.1:80', '2.2.2.2:80',]
    h.remove_host('localhost')
    assert h.hosts.keys() == ['2.2.2.2:80',]

    
    e = dict(HTTP_HOST = '2.2.2.2')
    assert h.dispatcher(e, {}) == 124
    
    print "[ALL TESTS PASSED]"

if __name__ == '__main__':
    run_test()

