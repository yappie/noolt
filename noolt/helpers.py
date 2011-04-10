import re
import os
import sys

import cjson
jse = cjson.encode
jsd = cjson.decode

def set_file(fn, txt):
    with open(fn, 'w') as f:
        f.write(txt)

class Print(object):
    def __init__(self, name):
        self.name = name
        self.msg = '?'

    def __enter__(self):
        print '<%s>' % self.name
        return self

    def __exit__(self, type1, value, traceback):
        if type1:
            print '</%s msg:"%s" exc:"%s">' % (self.name, self.msg, type1.__name__)
        else:
            print '</%s msg:"%s" no exc>' % (self.name, self.msg)

            
def reformat_traceback(self, exc):
    def escape(st):
        return st.replace('&','&amp;').replace('<','&lt;')
    exc_name, _, exc_explain = exc.strip().split('\n')[-1].partition(':')
    exc = re.sub(r'\n.*?runner\.py[^\n]+\n[^\n]+', '', exc)
    exc_name = exc_name.strip()
    exc_explain = exc_explain.strip()

    exc1 = '\n'.join(exc.strip().split('\n')[1:-1])
    html_exc = escape(exc1)

    comp = re.compile(r'\s*File "([^"]+)", line (\d+), in (\w+)\s*\n([^\n]+)')

    tb = ''
    list1 = comp.findall(exc1)
    list1.reverse()
    for fn, lineno, func, line in list1:
        
        tb += '<div class=where>def <span class=funcname>%s(...)</span>'\
            ' in .../%s/<span class=filename>%s</span></div>' % \
            (func, '/'.join(os.path.dirname(fn).split('/')[-2:]), 
            os.path.basename(fn))
        tb += '<ol class=codelines><li value="%d">%s</li></ol>' \
                 % (int(lineno), line)
    
    exc1 = comp.sub('', exc1)
    exc = re.sub(r'\n.*?runner\.py[^\n]+\n[^\n]+', '', exc)

    return """
    <style>
        .exception1 { 
            margin: 30px auto;
            width: 700px;
        }
        .exception { 
            font-family: sans; 
            background: white; 
            border-radius: 20px; 
            border: 4px solid #ffc000;
            -webkit-box-shadow: 
                0px 0px 20px rgba(97,14,25,.4), 
                0px 0px 8px rgba(97,14,25,.2);
            margin: 0; padding: 10px;
            background: #325a76
                -webkit-gradient(
                    linear,
                    left bottom,
                    left top,
                    color-stop(0.06, rgb(97,14,25)),
                    color-stop(0.75, rgb(209,7,7))
                );
        }
        .traceback_type { 
            font-size: 10px; color: #ffae00;
        }
        .traceback_explain { 
            color: #fffea6;
        }
        .traceback_word {
            font-size: 10px; padding: 6px; font-weight: bold;
        }
        .traceback { 
            padding: 7px; font-size: 13px; color: white;
            font-family: 'Courier New'; margin-top: 10px; 
            border-radius: 7px;
        }
        .where { font-size: 12px; line-height: 21px;}
        .codelines {
            background: #ffe9a6; 
            color: #000; 
            font-size: 14px;
            margin: 2px; 
            margin-bottom: 20px;
            font-weight: bold;
        }
        .codelines li {
            padding: 6px;
        }
        .funcname, .filename {
            font-weight: bold; 
            color: #ffe9a6;
        }
    </style>
    <div class=exception1>
        <div class=exception>
            <div style="font-size: 30px; font-weight: bold;">
                <span class=traceback_type>%s</span><br>
                <span class=traceback_explain>&ldquo;%s&rdquo;</span>
            </div>
            <div class=traceback>
                <div class=traceback_word>Traceback:</div>
                <pre>%s</pre>
            </div>
        </div>
    </div>
    """ % (exc_name, exc_explain, tb)
    
def relpath(path):
	return os.path.join(os.path.dirname(__file__),path)

