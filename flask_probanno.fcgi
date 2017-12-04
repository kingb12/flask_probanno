#!/local/local_webservices/flask_probanno/probannoenv/bin/python
activate_this = '/local/local_webservices/flask_probanno/probannoenv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
import sys
import os
sys.path.insert(0, '/local/local_webservices/flask_probanno')
os.environ["GUROBI_HOME"] = "/users/bking/gurobi751/linux64"
os.environ["LD_LIBRARY_PATH"] = os.environ["LD_LIBRARY_PATH"] + ":" + os.environ["GUROBI_HOME"] if "LD_LIBRARY_PATH" in os.environ else os.environ["GUROBI_HOME"]
os.environ["PATH"] = os.environ["PATH"] + ":" + os.environ["GUROBI_HOME"] + "/bin" if "PATH" in os.environ else os.environ["GUROBI_HOME"] + "/bin"
from flup.server.fcgi import WSGIServer
from flask_probanno import app
if __name__ == '__main__':
    WSGIServer(app).run()
