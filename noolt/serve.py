from noolt.app import App
import time
import glob
import os
import sys
import logging

# /usr/lib/python2.6/dist-packages/*.pth

class Apps:
    def __init__(self, developer_mode = False, base = '.'):
        self.apps = {}
        self.developer_mode = developer_mode
        self.base = base
        
    def load_more_apps(self):
        # XXX: maybe change to platform-dep.inotify
        for directory in glob.glob('*'): 
            index_fn = os.path.join(directory, 'index.py')
            if os.path.exists(index_fn):
                if directory not in self.apps:
                    self.apps[directory] = App(index_fn, self.developer_mode)
                    self.apps[directory].add_proc()
                    print 'Added app "%s"' % (index_fn,)
                    if self.developer_mode:
                        self.apps[directory].set_reload_intervals(.3)
            if not self.developer_mode:
                reload_fn = os.path.join(directory, '.reload')
                if os.path.exists(reload_fn):
                    os.unlink(reload_fn)
                    self.apps[directory].mark_processes_for_reload()
        # XXX: stop deleted apps

if __name__ == '__main__':
    try:
        dev_mode = False if '--production' in sys.argv else True
        apps = Apps(developer_mode = dev_mode, base = os.getcwd())
        while 1:
            apps.load_more_apps()
            time.sleep(1)
    except KeyboardInterrupt:
        print "Stopped"
        pass
