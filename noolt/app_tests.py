import time
import app
import helpers
import urllib

def run_wsgi_test(app):
    run_index = ''.join(u for u in app.on_wsgi({}, lambda x,y:1))
    return run_index
    
def run_tests_1():
    app = App('tests/test_1_app.py')
    assert app.procs[0].hosts == ['127.0.0.1:8081']
    assert not app.syntax_error()
    assert run_wsgi_test(app) == 'RAN INDEX\n'
    app.stop()
    try:
        run_wsgi_test(app)
        raise Exception('Should have raised Exception about no processes')
    except:
        pass

    app = App('tests/test_syntax_error.py')
    assert app.syntax_error()
    app.stop()

def run_tests_2_reloading():
    fn = 'tests/generated.py'
    helpers.set_file(fn, 'def index(r):\n print 1')
    app = App(fn)
    app.set_reload_intervals(-1)
    assert run_wsgi_test(app) == '1\n'
    helpers.set_file(fn, 'def index(r):\n print 2')
    assert run_wsgi_test(app) == '2\n'
    app.stop()

def run_tests_3_procs():
    fn = 'tests/generated.py'
    helpers.set_file(fn, 'import os\ndef index(r):\n print os.getpid()')
    app = App(fn)

    app.add_proc()
    pids = set([])
    for _ in range(20):
        pids.add(run_wsgi_test(app))
    assert len(pids) == 2
    
    app.del_proc()
    pids = set([])
    for _ in range(20):
        pids.add(run_wsgi_test(app))
    assert len(pids) == 1

    app.del_proc()
    try:
        run_wsgi_test(app)
        raise Exception('Should have raised Exception about no processes')
    except:
        pass
    
    app.stop()

    # crash process and auto-recover
    
    fn = 'tests/generated.py'
    helpers.set_file(fn, 'import sys\ndef index(r):\n print "crash-recovered"')
    app = App(fn)
    app.procs[0].chan.send_cmd('crash')
    assert 'crash-recovered' in run_wsgi_test(app)
    app.stop()

def run_tests_4_actual_httpd():
    fn = 'tests/generated.py'
    helpers.set_file(fn, 'hosts = ["127.0.0.1:8081"]\ndef index(r):\n print 1')

    app = App(fn)
    assert urllib.urlopen('http://127.0.0.1:8081/').read().strip() == '1'
    app.stop()
    try:
        urllib.urlopen('http://127.0.0.1:8081/').read().strip()
        raise Exception('Server did not stop properly')
    except IOError: 
        pass

   
    helpers.set_file(fn, 'hosts = ["127.0.0.1:8083"]\ndef index(r):\n print 1')
    app = App(fn)
    app.set_reload_intervals(-1)
    app.force_hosts_check()
    assert urllib.urlopen('http://127.0.0.1:8083/').read().strip() == '1'
    
    helpers.set_file(fn, 'hosts = ["127.0.0.1:8082"]\ndef index(r):\n print 2')
    app.force_hosts_check()
    assert urllib.urlopen('http://127.0.0.1:8082/').read().strip() == '2'
    
    app.stop()
    try:
        urllib.urlopen('http://127.0.0.1:8082/').read().strip()
        raise Exception('Server did not stop properly')
    except IOError: 
        pass

def run_tests_5_actual_httpd_multiprocess():
    fn = 'tests/generated.py'
    helpers.set_file(fn, 'hosts = ["127.0.0.1:8085"]\ndef index(r):\n print 1')
    app = App(fn)
    app.add_proc()
    app.add_proc()
    app.add_proc()
    app.set_reload_intervals(-1)
    app.force_hosts_check()
    for _ in range(10):
        assert urllib.urlopen('http://127.0.0.1:8085/').read().strip() == '1'
    
    helpers.set_file(fn, 'hosts = ["127.0.0.1:8085"]\ndef index(r):\n print 2')
    for _ in range(10):
        assert urllib.urlopen('http://127.0.0.1:8085/').read().strip() == '2'
    
    app.stop()
    try:
        urllib.urlopen('http://127.0.0.1:8085/').read().strip()
        raise Exception('Server did not stop properly')
    except IOError: 
        pass
        
def run_tests_6_back_to_same_host():
    fn = 'tests/generated.py'
    helpers.set_file(fn, 'hosts = ["127.0.0.1:8113"]\ndef index(r):\n print 1')
    app = App(fn)
    app.set_reload_intervals(-1)
    #app.force_hosts_check()
    assert urllib.urlopen('http://127.0.0.1:8113/').read().strip() == '1'
   
    helpers.set_file(fn, 'hosts = ["127.0.0.1:8112"]\ndef index(r):\n print 2')
    time.sleep(2) #app.force_hosts_check()
    assert urllib.urlopen('http://127.0.0.1:8112/').read().strip() == '2'

    helpers.set_file(fn, 'hosts = ["127.0.0.1:8113"]\ndef index(r):\n print 3')
    time.sleep(2) #app.force_hosts_check()
    try:
        assert urllib.urlopen('http://127.0.0.1:8113/').read().strip() == '3'
    finally:
        app.stop()

def run_tests_7_syntax_errors():
    fn = 'tests/generated.py'

    helpers.set_file(fn, 'hosts = "127.0.0.1:8090",\ndef index(r):\n print 1')
    app = App(fn)
    app.set_reload_intervals(-1)
    helpers.set_file(fn, 'hosts = "127.0.0.1:8090",\ndef index(r):\n print 1..')
    txt = urllib.urlopen('http://127.0.0.1:8090/').read()
    assert 'SyntaxError' in txt

    helpers.set_file(fn, 'hosts = "127.0.0.1:8090",\ndef index(r):\n print 1')
    assert urllib.urlopen('http://127.0.0.1:8090/').read().strip() == '1'

    app.stop()

    helpers.set_file(fn, 'hosts = "127.0.0.1:8091",\ndef index(r):\n print 1..')
    app = App(fn)
    app.set_reload_intervals(-1)
    try:
        txt = urllib.urlopen('http://127.0.0.1:8091/').read()
        raise Exception('Server started when it shouldn\'t have been.')
    except IOError:
        pass

    helpers.set_file(fn, 'hosts = "127.0.0.1:8091",\ndef index(r):\n print 1')
    app.force_hosts_check()
    assert urllib.urlopen('http://127.0.0.1:8091/').read().strip() == '1'

    app.stop()

        
def run_tests():
    
    App.httpds.running_tests = True
    run_tests_1()
    run_tests_2_reloading()
    run_tests_3_procs()

    App.httpds.running_tests = False
    run_tests_4_actual_httpd()
    run_tests_5_actual_httpd_multiprocess()
    run_tests_6_back_to_same_host()
    run_tests_7_syntax_errors()

    print "[ALL TESTS PASSED]"

if __name__ == '__main__':
    App = app.App
    run_tests()

