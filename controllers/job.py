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
GAPFILL_COMPLETE_URL = '/view/model/complete'
PROBANNO_COMPLETE_URL = '/view/probanno/complete'


class Job:

    def __init__(self, session_id, job, target, dummy=False):
        self.id = str(uuid.uuid4())
        self.status = NOT_STARTED
        self.job = job
        self.session = session_id
        self.target = target
        self.status = NOT_STARTED
        if not dummy:
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

    def to_dict_dto(self):
        return {
            "jid": self.id,
            "sid": self.session,
            "job": self.job,
            "target": self.target,
            "status": self.status
        }

    @classmethod
    def from_db_tuple(cls, tup):
        job = cls(tup[1], tup[2], tup[3], dummy=True)
        job.id = tup[0]
        job.status = tup[4]
        return job




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


def get_job(job_id):
    return Job.from_db_tuple(db.find_by_id(db.JOB, job_id))


def list_jobs():
    session_id = session_management.get_session_id()
    return json.dumps(db.list_jobs(session_id))


def view_status():
    job_id = request.args['job_id'] if 'job_id' in request.args else (request.form['job_id'] if 'job_id' in request.form else None)
    if job_id is None:
        return InvalidUsage("Must specify a job ID")
    job_entry = db.find_by_id(db.JOB, job_id)
    job_type = job_entry[2]
    target = job_entry[3]
    success_url = ''
    if job_type == 'calculate_probanno':
        success_url = PROBANNO_COMPLETE_URL + '?fasta_id=' + target
    else:
        success_url = GAPFILL_COMPLETE_URL + '?model_id=' + target
    return job_status_page(job_id, success_url)
