import time

hosts = ['127.0.0.1:8081',]

def index(r):
    print "RAN INDEX"
    
def print_2():
    print "2"
    
def do_exception():
    raise IOError
    
def print_and_exception():
    print "TEST123 PRINT"
    raise Exception("Test123 exception")
    
def print3times():
    print 1 # will be aborted
    time.sleep(1)
    print 2
    time.sleep(1)
    print 3
        
