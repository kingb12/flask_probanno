import sys
activate_this = '/users/bking/flask_probanno/probanno_env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
sys.path.insert(0, '/ebs/ProbannoModeling/flask_probanno')
from flask_probanno import app as application
