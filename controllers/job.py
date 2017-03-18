import uuid
from flask import request, abort, send_from_directory, render_template
from exceptions import InvalidUsage
from redis import Redis
from rq import Queue
import probanno
import session_management
import data.database as db
import utils
import json

COMPLETE = 'Complete'
FAILURE = 'Failure'
RUNNING = 'Running'
NOT_STARTED = 'Not Started'
JOB_ID = "job_id"

class Job:

    def __init__(self, session_id, job, target):
        self.id = str(uuid.uuid4())
        self.status = NOT_STARTED
        self.job = job
        self.session = session_id
        self.target = target
        self.status = NOT_STARTED
        self.update_job()

    def update_job(self):
        if db.find_by_id(db.JOB, self.id) is not None:
            db.update_job(self.id, self.session, self.job, self.target, self.status)
        else:
            db.insert_job(self.id, self.session, self.job, self.target, self.status)

    def start(self):
        self.status = RUNNING
        self.update_job()

    def complete(self):
        self.status = COMPLETE
        self.update_job()

    def fail(self):
        self.status = FAILURE
        self.update_job()


def check_job():
    if JOB_ID in request.args:
        job = db.find_by_id(db.JOB, request.args[JOB_ID])
    elif JOB_ID in request.form:
        job = db.find_by_id(db.JOB, request.form[JOB_ID])
    else:
        raise InvalidUsage("Must Supply a job ID")
    return json.dumps(job[-1])  # last column is status


def job_status_page(job_id, success_url):
    return render_template("check_job.html", job_id=job_id, success_url=success_url)
