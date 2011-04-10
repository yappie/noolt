`noolt` is an web application server with REAL and QUICK reloading, like in PHP 
(`noolt` actually spawns new processes for each application)

Quick example `server.py`

    from noolt.app import App
    import time
    
    app = App('hello_world.py')
    app.set_reload_intervals(.3)  # reload AT MOST ~3 times per second 
    
    time.sleep(1000000000)

`hello_world.py`

    hosts = "127.0.0.1:8091",
    
    def index(r):
        print "Hello, World"

Run `python server.py`
    
Then make changes to `hello_world.py` and instantly see changes appear.
`hosts` define host and port which the application will respond (you can change
those "on-fly") and even have many hosts/ports for each application.

If you install `noolt` to system path you can start from your "apps" directory:

    python -m noolt.serve --production
    
and then you can create directories with `index.py` file in them and have
them auto-served by `noolt`.

I haven't developed `noolt` in quite some time, but I feel it might be useful.
`noolt` uses CherryPy's excellent WSGI server.
