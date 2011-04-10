`noolt` is an web application server with REAL and QUICK reloading, like in PHP 
(`noolt` actually spawns new processes for each application). Reloading isn't
as simple as you could think - see [here](http://bugs.python.org/issue9072#msg108558)
for information from Python developers that started me on this quest.

Example
=======

Go into some directory, where you would be creating your "apps", like `~/web/`:
After installing noolt, run from console (terminal):

    mkdir ~/web/
    cd ~/web/
    python -m noolt.serve

Create file `~/web/app1/index.py` (`mkdir ~/web/app1 && gedit ~/web/app1/index.py`) with these contents:

    hosts = "127.0.0.1:8091",
    
    def index(r):
        print "Hello, World"

Go to http://127.0.0.1:8091/ in your browser. Change something in `~/web/app1/index.py` 
and see it instantly reload. By default `noolt` is configured to check for reloading
only at most 3 times per second, which is fast enough to be used in most 
production installations. See below on how to change it.

Installation
============

    git clone git://github.com/yappie/noolt.git noolt
    cd noolt
    sudo python setup.py install
    cd ..
    sudo rm -rf noolt
    

python -m noolt.serve
=====================

What this does is looks for new directories that have `index.py` in them, then
it scans for `hosts` variable and starts http servers accordingly. You might 
need super-user rights to run on port 80 (default http port).

More low-level example
======================

Quick example `server.py` (this is most of what `python -m noolt.serve` 
does for you).

    from noolt.app import App
    import time
    
    app = App('hello_world.py')
    app.set_reload_intervals(.3)  # reload AT MOST ~3 times per second 
    
    time.sleep(1000000000)

`hello_world.py`

    hosts = ("127.0.0.1:8091",)
    
    def index(r):
        print "Hello, World"

Run: 

    python server.py
    
Then make changes to `hello_world.py` and instantly see changes appear.
`hosts` define host and port which the application will respond (you can change
those "on-fly") and even have many hosts/ports for each application.

I haven't developed `noolt` in quite some time, but I feel it might be useful.

`noolt` uses CherryPy's excellent WSGI server.

Missing features
================

File upload not wrapped yet, but it's somewhere in the `r` variable.

r variable
==========

Variable that gets sent to `index` function is like this:

    r.wsgi = {
     'ACTUAL_SERVER_PROTOCOL': 'HTTP/1.1',
     'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
     'HTTP_ACCEPT_CHARSET': 'windows-1251,utf-8;q=0.7,*;q=0.3',
     'HTTP_ACCEPT_ENCODING': 'gzip,deflate,sdch',
     'HTTP_ACCEPT_LANGUAGE': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4',
     'HTTP_CACHE_CONTROL': 'max-age=0',
     'HTTP_CONNECTION': 'keep-alive',
     'HTTP_COOKIE': '....',
     'HTTP_HOST': '127.0.0.1:8091',
     'HTTP_USER_AGENT': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.27 (KHTML, like Gecko) Chrome/12.0.712.0 Safari/534.27',
     'PATH_INFO': '/',
     'QUERY_STRING': '',
     'REMOTE_ADDR': '127.0.0.1',
     'REMOTE_PORT': '46824',
     'REQUEST_METHOD': 'GET',
     'SCRIPT_NAME': '',
     'SERVER_NAME': 'localhost',
     'SERVER_PORT': '8091',
     'SERVER_PROTOCOL': 'HTTP/1.1',
     'SERVER_SOFTWARE': 'CherryPy/3.1.2 WSGI Server',
     'wsgi.multiprocess': False,
     'wsgi.multithread': True,
     'wsgi.run_once': False,
     'wsgi.url_scheme': 'http',
     'wsgi.version': [1, 0]
    }

so you can refer to those like this: `r.wsgi['HTTP_HOST']`

Suppressing tracebacks
======================

Currently this can only be done via "low level" (see above) by setting:

    def quiet_traceback(traceback_text):
        return ""

    app.reformat_traceback = quiet_traceback
    
Basically `reformat_traceback` receives text representation of traceback

Controlled production
=====================

Most of production environment could use usual `noolt` reloading, here is a more
strict version, that uses flag file to detect when to reload (redefine `is_production`
yourself somehow):

    from noolt.app import App
    import time, os
    
    is_production = True if os.path.exists('.production') else False

    app_filename = 'hello_world.py'
    reload_flag_filename = '.reload'

    app = App(app_filename)
    if is_production:
        app.set_reload_intervals(-1)  # do not reload
        app.reformat_traceback = lambda x: True
        while 1:
            if os.path.exists(reload_flag_filename):
                os.unlink(reload_flag_filename)
                app.mark_processes_for_reload()
            time.sleep(1)
    else:
        app = App(app_filename)
        app.set_reload_intervals(.3) 
        time.sleep(1000000000)


