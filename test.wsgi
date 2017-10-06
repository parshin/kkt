import sys
from conf import *

sys.path.append('/var/www/kkt_shared')
sys.path.append('/var/www/wsgi-scripts')
sys.path.append('/var/www')


def application(environ, start_response):
    status = '200 OK'
    output = 'Hello World!\n'
    output = output + params["IPAddress"] + '\n'
    output = output + str(sys.path) + '\n'
    output = output + __file__ + '\n'

    if environ['REQUEST_METHOD'] == 'POST':
        output = output + 'Post data:'
        output = output + (environ['wsgi.input'].read())

    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]
