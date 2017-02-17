from flask import request, flash, redirect
from werkzeug.utils import secure_filename
import os


# Utility files are silly. Develop this with caution
def upload_file(app, request_file, allowed_types=None):
    # if user does not select file, browser also
    # submit a empty part without filename
    file_name = None
    print request_file.filename
    if request_file.filename == '' or request_file.filename is None:
        flash('No selected file')
        return redirect(request.url)
    if request_file and allowed_file(request_file.filename, allowed_types):
        file_name = secure_filename(request_file.filename)
        request_file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))
    return file_name


def allowed_file(filename, allowed_types):
    return allowed_types is None or '.' in filename and \
           filename.rsplit('.', 1)[1] in allowed_types