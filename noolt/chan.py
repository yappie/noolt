import sys
import subprocess
import select
import threading
import time
import helpers
jse = helpers.jse
jsd = helpers.jsd

def log(*args): sys.stderr.write(' '.join(map(unicode, args)) + '\n')

class ChanBase:
    def __init__(self, In = None, Out = None):
        self.transaction = threading.Lock()
        self.set_channels(In, Out)
        
    def run_file(self, args):
        self.run_args = args
        self.process = subprocess.Popen(args,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            )
        self.In = self.process.stdout
        self.Out = self.process.stdin
        
    def send_cmd(self, action, **kwargs):
        kwargs['action'] = action
        #log('SEND %s' % jse(kwargs))
        #if __file__ == 'chan.py':
        #    print "runn?", jse(kwargs)
        self.Out.write(jse(kwargs))
        self.Out.write('\n')
        self.Out.flush()
        
    def recv_cmd(self):
        while True:
            line = self.In.readline()
            if not line: break
            if line[0] == '{': break
            print "RECVd gibberish", line
            
        if not line: raise IOError('Channel closed?')
        cmd = jsd(line)
        return cmd
    
    def restart(self):
        self.close()
        self.run_file(self.run_args)
        
    def query(self, cmd):
        with self.transaction:
            #with helpers.Print('query') as f:
                self.send_cmd(action = cmd)
                ret = self.recv_cmd()
                return ret['value']
        
    def close(self):
        try:
            self.send_cmd('shutdown')
            line = self.In.readline()
        except IOError:
            line = ''
        if line == '':
            return True
        else:
            raise Exception('Chan did not close, sent extra: [%s]' % line)

    def set_channels(self, In, Out):
        with self.transaction:
            self.In = In
            self.Out = Out
        

class Chan(ChanBase):
    def get_locals(self, var):
        with self.transaction:
            self.send_cmd('get_locals', var = var)
            return self.recv_cmd()['val']

    def run_file(self, args):
        with self.transaction:
            ChanBase.run_file(self, args)
            cmd = self.recv_cmd()
            if cmd['action'] == 'ready':
                return
            elif cmd['action'] == 'exception':
                if 'IOError' in cmd['string']:
                    raise IOError()
                else:
                    raise Exception('\n' + cmd['string'])

    def run_func(self, func, args):
        with self.transaction:
            #with helpers.Print('runfunc'):
                self.send_cmd('run_func', func = func, args = args)
                while 1:
                    cmd = self.recv_cmd()
                    if cmd['action'] == 'done':
                        return
                    yield cmd
                    if cmd['action'] == 'exception':
                        return

    def poll_read(self):
        return True if select.select([self.In,], [], [], 0)[0] else False

def run_test_1():
    c = Chan()
    c.run_file(['python', 'runner.py', 'tests/test_1_app.py'])
    assert c.get_locals('hosts') == ['127.0.0.1:8081']
    pid1 = c.process.pid

    c.restart()
    assert c.get_locals('hosts') == ['127.0.0.1:8081']
    assert pid1 != c.process.pid

    ret = ''.join(repr(u) for u in c.run_func('print_2', ()))
    assert "stdout', 'string': '2'" in ret

    ret = ''.join(repr(u) for u in c.run_func('do_exception', ()))
    assert 'IOError' in ret

    c.close()
    try:
        c.send_cmd('test')
        raise Exception('Should raise IOError')
    except IOError:
        pass

    c = Chan()
    c.run_file(['python', 'runner.py', 'tests/test_1_app.py'])
    for u in c.run_func('print_2', ()):
        pass
    for u in c.run_func('print_2', ()):
        pass
    c.close()
    


def run_test_2():
    c = Chan()
    try:
        c.run_file(['python', 'runner.py', 'tests/doesnt_exist.py'])
        raise Exception("Should raise IOError")
    except:
        pass
    c.close()
    
    c = Chan()
    try:
        c.run_file(['python', 'runner.py', 'tests/test_syntax_error.py'])
        raise Exception("Should raise Exception")
    except:
        pass
    c.close()


def run_test():
    run_test_1()
    run_test_2()
    print "[ALL TESTS PASSED]"

if __name__ == '__main__':
    run_test()

