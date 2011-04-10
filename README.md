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

Run `python server.py`
    
Then make changes to `hello_world.py` and instantly see changes appear.
`hosts` define host and port which the application will respond (you can change
those "on-fly") and even have many hosts/ports for each application.

I haven't developed `noolt` in quite some time, but I feel it might be useful.
`noolt` uses CherryPy's excellent WSGI server.
