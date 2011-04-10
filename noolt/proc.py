import time
import traceback
import threading
import helpers
import random
from chan import Chan

class Proc(object):
    """
    One of the processes that runs the copy of app
    """
    def __init__(self, app, run_args):
        self.marked_for_reload = 0
        self.proc_lock = threading.Lock()
        self.hosts = []
        self.print_tracebacks = False
        self.new_host_check_interval = -1

        self.app = app
        self.stopping = 0
        self.wsgis_active = 0

        self.chan = Chan()
        self.syntax_error = None
        try:
            self.chan.run_file(run_args)
        except Exception, e:
            print "Can't run file '%s' (probably syntax errors), "\
                  "and possibly can't detect it's hosts" % self.app.fn
            self.syntax_error = e.args[0]#traceback.format_exc()
            
        self.app.on_proc_restarted(self)
        
        self.force_hosts_check()

    def force_hosts_check(self, once = False):
        with self.proc_lock:
            if not self.stopping:
                self.reload_if_needed()
                if not once:
                    check_again_in = self.new_host_check_interval
                    # to make sure processes check sources somewhat uniformly
                    check_again_in = random.uniform(.9,1.1)
                    if check_again_in < .00001: check_again_in = .1
                    threading.Timer(check_again_in, 
                                    self.force_hosts_check).start()
        
    def stop(self):
        with self.proc_lock:
            self.stopping = 1
        while self.wsgis_active > 0:
            time.sleep(.01)
        self.chan.close()

    def handle_traceback(self, txt):
        if self.print_tracebacks:
            return self.app.reformat_traceback(txt)
        else:
            return ''

    def on_wsgi(self, e, s):
        try:
            self.wsgis_active += 1
            with self.proc_lock:
                self.reload_if_needed()
                
                headers = { 'Content-type': 'text/html' }
                headers_sent = False

                if self.syntax_error:
                    s('200 Ok', [('Content-type', 'text/html',)]) 
                    yield self.handle_traceback(self.syntax_error)
                    return

                client_connected = 1
                run = self.chan.run_func('index', self.index_args_from_e(e))
                for item in run:
                    if client_connected:
                        try:                    
                            if item['action'] == 'stdout' or \
                                    item['action'] == 'binary':
                                if item['action'] == 'binary':
                                    # XXX: ineffective binary handling!
                                    item['string'] = uni2str(item['string'])
                                if not headers_sent:
                                    headers_sent = True
                                    s('200 Ok', headers.items())
                                yield item['string']
                                
                            elif item['action'] == 'header':
                                if headers_sent:
                                    yield self.handle_traceback('Headers were already sent')
                                    raise GeneratorExit()

                                else:
                                    if ':' in item['string']:
                                        h,_,v = item['string'].partition(': ')
                                        if h.lower() == 'content-type':
                                            h = 'Content-type'
                                        headers[h] = v

                            elif item['action'] == 'exception':
                                if not headers_sent:
                                    headers_sent = True
                                    s('200 Ok', headers.items())
                                exc = item['string']
                                yield self.handle_traceback(exc)

                            else:
                                raise NotImplementedError
                        except GeneratorExit:
                            self.chan.send_cmd('abort')
                            client_connected = 0
        except:
            raise
        finally:
            self.wsgis_active -= 1

    def reload_if_needed(self):
        with self.app.lock:
            if not self.marked_for_reload:
                try:
                    need_reload = self.chan.query('source_changed')
                except IOError:
                    need_reload = 1
                    
                if need_reload:
                    self.app.mark_processes_for_reload()

            if self.marked_for_reload > 0:
                self.syntax_error = None
                try:
                    #print "Restarting"
                    self.chan.restart()
                except Exception, e:
                    self.syntax_error = e[0]
                    
                self.app.on_proc_restarted(self)
                self.marked_for_reload -= 1

    def index_args_from_e(self, e):
        r = dict(wsgi = e)
        if 'wsgi.errors' in r['wsgi']:
            del r['wsgi']['wsgi.errors']
        if 'wsgi.input' in r['wsgi']:
            del r['wsgi']['wsgi.input']
        return (r,)


# tests: Proc depends heavily on App, so all of the testing is done in App

def uni2str(st):
    return ''.join(chr(ord(c)) for c in st)

