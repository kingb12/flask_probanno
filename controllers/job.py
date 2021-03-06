import json
import uuid
from exceptions import InvalidUsage

from flask import request, abort, render_template, jsonify

import data.database as db
import session_management
from controllers.error_management import missing_argument, not_found

COMPLETE = 'Complete'
FAILURE = 'Failure'
RUNNING = 'Running'
NOT_STARTED = 'Not Started'
JOB_ID = "job_id"
GAPFILL_COMPLETE_URL = '/view/model/complete'
PROBANNO_COMPLETE_URL = '/view/probanno/complete'


class Job:

    def __init__(self, session_id, job, target, status=NOT_STARTED, dummy=False):
        self.id = str(uuid.uuid4())
        self.status = status
        self.job = job
        self.session = session_id
        self.target = target
        self.status = status
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
        if tup is None:
            return None
        job = cls(tup[1], tup[2], tup[3], dummy=True)
        job.id = tup[0]
        job.status = tup[4]
        return job


def check_job(job_id=None):
    if job_id is None:
        if JOB_ID in request.args:
            job = db.find_by_id(db.JOB, request.args[JOB_ID])
        elif JOB_ID in request.form:
            job = db.find_by_id(db.JOB, request.form[JOB_ID])
        else:
            raise InvalidUsage("Must Supply a job ID")
    else:
        job = db.find_by_id(db.JOB, job_id)
    if job is None:
        abort(404)
    return json.dumps(job[-1])  # last column is status


def job_status_page(job_id, success_url):
    return render_template("check_job.html", job_id=job_id, success_url=success_url)


def get_job():
    session = session_management.get_session_id()
    if session is None:
        return session_management.bad_or_missing_session()
    if JOB_ID not in request.args:
        return missing_argument(JOB_ID)
    job = retrieve_job(request.args[JOB_ID])
    if job is None:
        return not_found("Job not found")
    return jsonify(job.to_dict_dto())


def retrieve_job(job_id):
    return Job.from_db_tuple(db.find_by_id(db.JOB, job_id))


def list_jobs():
    session = session_management.get_session_id()
    if session is None:
        return session_management.bad_or_missing_session()
    jobs = [Job.from_db_tuple(job).to_dict_dto() for job in db.list_jobs(session)]
    return jsonify(jobs)


def view_status(job_id=None):
    if job_id is None:
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
