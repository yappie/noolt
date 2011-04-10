import sys
import os
import traceback
import threading
import re
import wsgi_dict_to_r_argument

from filewatcher import FileWatcher
from chan import Chan

import helpers
jse = helpers.jse
jsd = helpers.jsd


def log(*args): sys.stderr.write(' '.join(map(unicode, args)) + '\n')

class Runner:
    STOP = 0
    CONTINUE = 1
    
    def __init__(self, fn, In = None, Out = None):
        if In is None:  In = sys.stdin
        if Out is None: Out = sys.stdout
        self.fn = fn
        self.chan = Chan()
        self.chan.set_channels(In, Out)
        self.filewatch = FileWatcher(fn)

        self.code_locals = {}
        try:
            self.load_code(self.code_locals)
            self.filewatch.note_new_files()
            self.chan.send_cmd('ready')
        except:
            self.filewatch.note_new_files()
            self.chan.send_cmd('exception', string = traceback.format_exc())
       
    def run_cmd(self, cmd):
        if cmd['action'] == 'shutdown':
            return Runner.STOP
        elif cmd['action'] == 'get_locals':
            value = self.code_locals.get(cmd['var'], '')
            self.chan.send_cmd('locals', val = value)
        elif cmd['action'] == 'set_reload_interval':
            self.filewatch.interval = cmd['value']
        elif cmd['action'] == 'run_func':
            self.run_func(cmd)
        elif cmd['action'] == 'crash':
            sys.exit()
        elif cmd['action'] == 'abort': 
            # client disconnected, but script was finished by that time
            pass
        elif cmd['action'] == 'source_changed':
            value = 1 if self.filewatch.has_changed() else 0
            self.chan.send_cmd('', value = value)
        else:
            log('runner.py has idea was this incoming is:\n', repr(cmd))
            raise NotImplementedError
        
        return Runner.CONTINUE

    def loop(self):
        import time
        while 1:
            cmd = self.chan.recv_cmd()
            #log("Test %d %s\n" % (time.time(), repr(cmd)))
            if self.run_cmd(cmd) == Runner.STOP:
                return
            
    def load_code(self, my_locals):
        with open(self.fn) as f:
            code_src = f.read()
        try:
            self.code = compile(code_src, os.path.abspath(self.fn), 'exec')
        except Exception, e:
            hosts_line = re.findall('^(hosts\s*=[^\n]+)', code_src)
            if hosts_line:
                c = compile(hosts_line[0], '', 'exec')
                exec c in my_locals
            raise e
        exec self.code in my_locals
        
    def run_func(self, cmd):
        stdout_save = sys.stdout
        if cmd['func'] not in self.code_locals:
            self.chan.send_cmd('exception', string = \
                'NameError: No function named "%s" in "%s"' % \
                (cmd['func'], self.fn))
            return
                    
        try:
            func = self.code_locals[cmd['func']]
            sys.stdout = StreamRedirector(
                lambda x, chan = self.chan:chan.send_cmd('stdout', string = x),
                lambda chan = self.chan: poll_and_raise_on_abort_cmd(chan),
            )
            header_func = \
                lambda x, chan = self.chan:chan.send_cmd('header', string = x)
            binary_func = \
                lambda x, chan = self.chan:chan.send_cmd('binary', string = x)
            
            if cmd['func'] == 'index':
                cmd['args'][0] = wsgi_dict_to_r_argument.upgrade(cmd['args'][0])
                cmd['args'][0].header = header_func
                cmd['args'][0].binary = binary_func
            
            func(*cmd['args'])
            self.chan.send_cmd('done')
        except:
            self.chan.send_cmd('exception', string = traceback.format_exc())
        finally:
            sys.stdout = stdout_save

def poll_and_raise_on_abort_cmd(chan):
    if chan.poll_read():
        cmd = chan.recv_cmd()
        if cmd['action'] == 'abort':
            raise Exception('Client disconnect')

class StreamRedirector:
    def __init__(self, cb, cb2):
        self.cb = cb
        self.cb2 = cb2
        
    def write(self, string):
        self.cb(string)
        self.cb2()

def run_test():
    import StringIO
    def run_func_get_string(fn, func, args):
        out = StringIO.StringIO()
        r = Runner(fn, Out = out)
        r.run_cmd(dict(action = 'run_func', func = func, args = args))
        return out.getvalue()
    
    out = StringIO.StringIO()
    r = Runner('tests/test_1_app.py', Out = out)
    assert out.getvalue() == '{"action": "ready"}\n'
    
    txt = run_func_get_string('tests/test_1_app.py', 'print_2', [])
    assert '{"action": "stdout", "string": "2"}' in txt
    assert '{"action": "done"}' in txt, txt

    txt = run_func_get_string('tests/test_1_app.py', 'do_exception', [])
    assert '{"action": "exception",' in txt
    assert 'IOError' in txt

    txt = run_func_get_string('tests/test_1_app.py', 'print_and_exception', [])
    assert "TEST123 PRINT" in txt
    assert "Test123 exception" in txt
    assert '{"action": "done"}' not in txt

    assert r.run_cmd(dict(action = 'shutdown')) == Runner.STOP
    
    with open('tests/test.txt','w') as f:
        f.write(jse(dict(action = 'abort')))
    with open('tests/test.txt','r') as ins:
        out = StringIO.StringIO()
        r = Runner('tests/test_1_app.py', In = ins, Out = out)
        r.run_cmd(dict(action = 'run_func', func='print3times', args=()))
        assert 'Client disconnect' in out.getvalue()
    
    print "[ALL TESTS PASSED]"
    
def main():
    if len(sys.argv) == 1:
        run_test()
        return
        
    r = Runner(sys.argv[1])
    r.loop()

if __name__ == '__main__':
    main()

