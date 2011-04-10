import pprint

class HTTPRequest(object):
    def __init__(self, env):
        self.wsgi = env['wsgi']

    def __repr__(self):
        return 'HTTPRequest( self.wsgi = %s\n)\n' % pprint.pformat(self.wsgi)

def upgrade(env):
    return HTTPRequest(env)
