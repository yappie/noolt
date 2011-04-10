#
# Diagram for what includes what
#
#        App ------.
#       / |  \      `-.
#     /   |   \        \
#   Proc Proc Proc     HTTPds
#    |    |    |
#   Chan ...  ...
#    |    
#  Runner (separate process)
#    |
#  FileWatcher
#

import urllib
import time
import threading
import random
import os       

from httpds import HTTPds
from proc import Proc
import helpers

class App(object):
    httpds = HTTPds()
    
    def __init__(self, fn, print_tracebacks = False):
        self.lock = threading.Lock()
        self.fn = fn
        self.procs = []
        self.print_tracebacks = print_tracebacks
        self.set_reload_intervals(-1)
        self.run_args = self.run_args_from_fn(self.fn)
        self.add_proc()
        self.last_access = time.time()
    
    def add_proc(self):
        proc = Proc(self, self.run_args)
        proc.print_tracebacks = self.print_tracebacks
        new_hosts = proc.chan.get_locals('hosts') or []
        self.procs.append(proc)
        App.httpds.add_remove(self.on_wsgi, new_hosts, proc.hosts)
        proc.hosts = new_hosts
        self.set_reload_intervals()

    def del_proc(self):
        proc = self.procs.pop()
        App.httpds.add_remove(self.on_wsgi, [], proc.hosts)
        proc.stop()
        self.set_reload_intervals()
    
    def num_procs(self):
        return len(self.procs)
    
    def set_reload_intervals(self, ri = None):
        if ri:
            self.reload_interval = ri
            
        for proc in self.procs:
            proc.new_host_check_interval = self.reload_interval*len(self.procs)
            proc.chan.send_cmd('set_reload_interval', 
                                value = self.reload_interval*len(self.procs))
    
    def change_source(self):
        with self.lock:
            for proc in self.procs:
                proc.run_args = self.run_args_from_fn(self, fn)
            self.mark_processes_for_reload()
    
    def mark_processes_for_reload(self):
        for proc in self.procs:
            proc.marked_for_reload += 1
        
    def stop(self):
        while self.procs:
            self.del_proc()
        
    def on_proc_restarted(self, proc):
        new_httpds = proc.chan.get_locals('hosts') or []
        old_hosts = proc.hosts
        proc.hosts = new_httpds
        self.set_reload_intervals()
        if not proc.syntax_error:
            self.start_stop_httpds(new_httpds, old_hosts)
        self.set_reload_intervals()
        
    def find_available_wsgi(self, e, s):
        return list(i for i in self.procs if not i.stopping)

    def since_last_access(self):
        return time.time() - self.last_access        

    def on_wsgi(self, e, s):
        self.last_access = time.time()
        proc = self.find_available_wsgi(e, s)
        if not proc:
            raise Exception('No processes available to respond')
        return random.choice(proc).on_wsgi(e, s)

    def run_args_from_fn(self, fn):
        return ['python', helpers.relpath('runner.py'), fn]

    def start_stop_httpds(self, new, old):
        App.httpds.add_remove(self.on_wsgi, new, old)
        #self.hosts = new
    
    def syntax_error(self):
        return any(i.syntax_error for i in self.procs)
        
    def force_hosts_check(self):
        for proc in self.procs:
            proc.force_hosts_check(once = True)

    reformat_traceback = helpers.reformat_traceback

if __name__ == '__main__':
    #execfile('app_tests.py')

    fn = 'tests/editable.py'
    #helpers.set_file(fn, 'hosts = "127.0.0.1:8090",\n\\\\')
    app = App(fn)
    app.set_reload_intervals(-1)
    app.del_proc()
    print app.num_procs()
    app.add_proc()
    #app.mark_processes_for_reload()
    #print app.since_last_access()
    
    while 1:
        time.sleep(1)

