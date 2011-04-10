import sys
import os
import time

class FileWatcher:
    def __init__(self, base_fn):
        self.fn = base_fn
        self.interval = 0.5
        self.watch = {}
        self.last_check = time.time()
        self.base = self._module_files_set()

    def _module_files_set(self):
        filename = lambda m:getattr(m, '__file__', None)
        return set(filename(m) for m in sys.modules.itervalues() if filename(m))
        
    def filemtimes(self, files):
        return dict((f, os.path.getmtime(f)) for f in files)
        
    def note_new_files(self):
        files = self._module_files_set() - self.base
        files.add(self.fn)
        self.watch = self.filemtimes(files)
        self.last_check = time.time()

    def has_changed(self):
        if time.time() - self.last_check >= self.interval:
            self.last_check = time.time()
            watch = self.filemtimes(self.watch.keys())
            for fn in watch:
                if watch[fn] > self.watch[fn]:
                    return True

def run_test():
    fn = 'tests/test_1_app.py'
    fw = FileWatcher(fn)
    fw.interval = -1
    fw.note_new_files()
    assert not fw.has_changed()
    os.utime(fn, None)
    assert fw.has_changed()
    print "[ALL TESTS PASSED]"

if __name__ == '__main__':
    run_test()

