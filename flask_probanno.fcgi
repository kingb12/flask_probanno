#!/local/local_webservices/flask_probanno/probannoenv/bin/python
activate_this = '/local/local_webservices/flask_probanno/probannoenv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
import sys
sys.path.insert(0, '/local/local_webservices/flask_probanno')
from flup.server.fcgi import WSGIServer
from flask_probanno import app
if __name__ == '__main__':
    WSGIServer(app).run()
