import requests
import unittest
import json
import uuid

from flask_probanno import GET, POST, PUT
from controllers.probanno_management import CALCULATE_PROBANNO_JOB
from controllers.job import COMPLETE

BASE_URL = "http://probannoweb.systemsbiology.net/api"
HEADERS = {'cache-control': 'no-cache'}
FASTA_1 = '267377'
CACHED_FASTA = '243232'
CACHED_FASTA_NAME = 'Methanocaldococcus jannaschii (strain ATCC 43067 / DSM 2661 / JAL-1 / JCM 10045 / NBRC 100440)'
NOT_A_FASTA = 'abcdef'
MY_FASTA_NAME = 'my_sequence'
TEST_MODEL_FILE = 'maripaludis_model.json'
GAPFILL_MODEL_JOB = "gapfill_model"


class TestSessionMethods(unittest.TestCase):

    def test_get_session(self):
        try:
            session = make_and_unpack_request("/session", GET, HEADERS)
            # exception below indicates failure
            my_uuid = uuid.UUID(session)
        finally:
            clear_session_values(session, clear_session=True)


class TestProbannoMethods(unittest.TestCase):

    def test_calculate_likelihoods_get(self):
        session = make_and_unpack_request("/session", GET, HEADERS)
        try:
            # un-cached
            job = make_and_unpack_request("/probanno/calculate", GET, authorize_headers(session), params={"fasta_id": FASTA_1})
            assert job['sid'] == session
            assert job['job'] == CALCULATE_PROBANNO_JOB
            assert job['target'] == FASTA_1
            # cached
            job = make_and_unpack_request("/probanno/calculate", GET, authorize_headers(session), params={"fasta_id": CACHED_FASTA})
            assert job['sid'] == session
            assert job['job'] == CALCULATE_PROBANNO_JOB
            assert job['target'] == CACHED_FASTA
            assert job['status'] == COMPLETE
            # 404 FASTA not found
            response = make_api_request("/probanno/calculate", GET, authorize_headers(session),
                                   params={"fasta_id": NOT_A_FASTA})
            assert response.status_code == 404
            # 400 No session
            response = make_api_request("/probanno/calculate", GET, HEADERS,
                                        params={"fasta_id": FASTA_1})
            # 400 bad session
            response = make_api_request("/probanno/calculate", GET, authorize_headers(str(uuid.uuid4())),
                                        params={"fasta_id": FASTA_1})
            assert response.status_code == 400
        finally:
            # clean up
            clear_session_values(session, clear_session=True)

    def test_calculate_likelihoods_put(self):
        session = make_and_unpack_request("/session", GET, HEADERS)
        try:
            # remove any values that would have been cached
            clear_probanno(FASTA_1)
            files = {'fasta': open('267377.fasta', 'rb')}
            data = {'fasta_id': MY_FASTA_NAME}
            # un-cached
            job = make_and_unpack_request("/probanno/calculate", PUT, authorize_headers(session), files=files, data=data)
            assert job['sid'] == session
            assert job['job'] == CALCULATE_PROBANNO_JOB
            assert job['target'] == MY_FASTA_NAME
            # 400 no FASTA
            response = make_api_request("/probanno/calculate", PUT, authorize_headers(session),
                                   data=data)
            # 400 no FASTA_ID
            response = make_api_request("/probanno/calculate", PUT, authorize_headers(session),
                                        files=files)
            assert response.status_code == 400
            # 400 No session
            response = make_api_request("/probanno/calculate", PUT, HEADERS,
                                        params={"fasta_id": FASTA_1})
            assert response.status_code == 400
            # 400 bad session
            response = make_api_request("/probanno/calculate", PUT, authorize_headers(str(uuid.uuid4())),
                                        params={"fasta_id": FASTA_1})
            assert response.status_code == 400
        finally:
            # clean up
            clear_session_values(session, clear_session=True)

    def test_get_likelihoods(self):
        session = make_and_unpack_request("/session", GET, HEADERS)
        try:
            # search for, expect missing
            response = make_api_request("/probanno", GET, authorize_headers(session),
                                          params={"fasta_id": CACHED_FASTA})
            assert(response.status_code == 404)
            # cached: populate it for our session
            job = make_and_unpack_request("/probanno/calculate", GET, authorize_headers(session),
                                          params={"fasta_id": CACHED_FASTA})
            assert job['sid'] == session
            assert job['job'] == CALCULATE_PROBANNO_JOB
            assert job['target'] == CACHED_FASTA
            assert job['status'] == COMPLETE

            # Now actually check retrieval
            result = make_and_unpack_request("/probanno", GET, authorize_headers(session),
                                          params={"fasta_id": CACHED_FASTA})
            assert(type(result) == list)
            # 400 No session
            response = make_api_request("/probanno", GET, HEADERS,
                                        params={"fasta_id": FASTA_1})
            assert response.status_code == 400
            # 400 bad session
            response = make_api_request("/probanno", GET, authorize_headers(str(uuid.uuid4())),
                                        params={"fasta_id": FASTA_1})
            assert response.status_code == 400
            response = make_api_request("/probanno", GET, HEADERS,
                                        params=None)
            assert response.status_code == 400
            response = make_api_request("/probanno", GET, authorize_headers(session),
                                        params={"fasta_id": NOT_A_FASTA})
            assert response.status_code == 404

        finally:
            # clean up
            clear_session_values(session, clear_session=True)

    def test_list_likelihoods(self):
        session = make_and_unpack_request("/session", GET, HEADERS)
        try:
            # search for, expect missing
            result = make_and_unpack_request("/probanno/list", GET, authorize_headers(session),
                                          params={"fasta_id": CACHED_FASTA})
            assert(len(result) == 0 and type(result) == list)
            # cached: populate it for our session
            job = make_and_unpack_request("/probanno/calculate", GET, authorize_headers(session),
                                          params={"fasta_id": CACHED_FASTA})
            assert job['sid'] == session
            assert job['job'] == CALCULATE_PROBANNO_JOB
            assert job['target'] == CACHED_FASTA
            assert job['status'] == COMPLETE

            # Now actually check retrieval
            result = make_and_unpack_request("/probanno/list", GET, authorize_headers(session),
                                          params={"fasta_id": CACHED_FASTA})
            assert(type(result) == list)
            assert(len(result) == 1)
            assert(type(result[0]) == dict)
            assert(result[0]['name'] == CACHED_FASTA_NAME)
            assert(result[0]['fasta_id'] == CACHED_FASTA)

            # 400 No session
            response = make_api_request("/probanno/list", GET, HEADERS,
                                        params={"fasta_id": FASTA_1})
            assert response.status_code == 400
            # 400 bad session
            response = make_api_request("/probanno/list", GET, authorize_headers(str(uuid.uuid4())),
                                        params={"fasta_id": FASTA_1})
            assert response.status_code == 400
        finally:
            # clean up
            clear_session_values(session, clear_session=True)

    def test_download_likelihoods(self):
        session = make_and_unpack_request("/session", GET, HEADERS)
        try:
            # search for, expect missing
            response = make_api_request("/probanno/download", GET, authorize_headers(session),
                                          params={"fasta_id": CACHED_FASTA})
            assert(response.status_code == 404)
            # cached: populate it for our session
            job = make_and_unpack_request("/probanno/calculate", GET, authorize_headers(session),
                                          params={"fasta_id": CACHED_FASTA})
            assert job['sid'] == session
            assert job['job'] == CALCULATE_PROBANNO_JOB
            assert job['target'] == CACHED_FASTA
            assert job['status'] == COMPLETE

            # Now actually check retrieval
            result = make_api_request("/probanno/download", GET, authorize_headers(session),
                                          params={"fasta_id": CACHED_FASTA})
            assert(type(result.content) == str)
            assert (type(json.loads(result.content) == list))
            # 400 No session
            response = make_api_request("/probanno", GET, HEADERS,
                                        params={"fasta_id": FASTA_1})
            assert response.status_code == 400
            # 400 bad session
            response = make_api_request("/probanno", GET, authorize_headers(str(uuid.uuid4())),
                                        params={"fasta_id": FASTA_1})
            assert response.status_code == 400
        finally:
            # clean up
            clear_session_values(session, clear_session=True)


class TestModelMethods(unittest.TestCase):

    def test_get_model(self):
        model_id = "my_model"
        session = make_and_unpack_request("/session", GET, HEADERS)
        try:
            # search for, expect missing
            response = make_api_request("/model", GET, authorize_headers(session),
                                        params={"model_id": model_id})
            assert (response.status_code == 404)
            # cached: populate it for our session
            job = None
            with open(TEST_MODEL_FILE, 'rb') as f:
                response = make_api_request("/model", PUT, authorize_headers(session),
                                          data={"model_id": model_id}, files={"file": f})
            assert(response.status_code == 200)

            # Now actually check retrieval
            result = make_and_unpack_request("/model", GET, authorize_headers(session),
                                             params={"model_id": model_id})
            assert (type(result) == dict)
            # 400 No session
            response = make_api_request("/model", GET, HEADERS,
                                        params={"model_id": model_id})
            assert response.status_code == 400
            # 400 bad session
            response = make_api_request("/model", GET, authorize_headers(str(uuid.uuid4())),
                                        params={"model_id": model_id})
            assert response.status_code == 400
            response = make_api_request("/model", GET, HEADERS,
                                        params=None)
            assert response.status_code == 400
            response = make_api_request("/model", GET, authorize_headers(session),
                                        params={"model_id": NOT_A_FASTA})
            assert response.status_code == 404
        finally:
            # clean up
            clear_session_values(session, clear_session=True)

    def test_download_model(self):
        model_id = "my_model"
        session = make_and_unpack_request("/session", GET, HEADERS)
        try:
            # search for, expect missing
            response = make_api_request("/model/download", GET, authorize_headers(session),
                                        params={"model_id": model_id})
            assert (response.status_code == 404)
            # cached: populate it for our session
            job = None
            with open(TEST_MODEL_FILE, 'rb') as f:
                response = make_api_request("/model", PUT, authorize_headers(session),
                                            data={"model_id": model_id}, files={"file": f})
            assert (response.status_code == 200)

            # Now actually check retrieval
            result = make_api_request("/model/download", GET, authorize_headers(session),
                                             params={"model_id": model_id})
            assert (type(result.content) == str)
            assert(type(json.loads(result.content) == dict))
            # 400 No session
            response = make_api_request("/model/download", GET, HEADERS,
                                        params={"model_id": model_id})
            assert response.status_code == 400
            # 400 bad session
            response = make_api_request("/model/download", GET, authorize_headers(str(uuid.uuid4())),
                                        params={"model_id": model_id})
            assert response.status_code == 400
            response = make_api_request("/model/download", GET, HEADERS,
                                        params=None)
            assert response.status_code == 400
            response = make_api_request("/model/download", GET, authorize_headers(session),
                                        params={"model_id": NOT_A_FASTA})
            assert response.status_code == 404
        finally:
            # clean up
            clear_session_values(session, clear_session=True)

    def test_model_put(self):
        model_id = "my_model"
        session = make_and_unpack_request("/session", GET, HEADERS)
        f = open(TEST_MODEL_FILE, 'rb')
        try:
            # search for, expect missing
            response = make_api_request("/model", GET, authorize_headers(session),
                                        params={"model_id": model_id})
            assert (response.status_code == 404)
            # cached: populate it for our session
            response = make_api_request("/model", PUT, authorize_headers(session),
                                            data={"model_id": model_id}, files={"file": f})
            assert (response.status_code == 200)

            # Update Case
            f = open(TEST_MODEL_FILE, 'rb')
            response = make_api_request("/model", PUT, authorize_headers(session),
                                            data={"model_id": model_id}, files={"file": f})
            assert (response.status_code == 200)

            # Now actually check retrieval
            result = make_and_unpack_request("/model", GET, authorize_headers(session),
                                             params={"model_id": model_id})
            assert (type(result) == dict)
            # 400 No session
            response = make_api_request("/model", PUT, HEADERS,
                                        data={"model_id": model_id}, files={"file": f})
            assert response.status_code == 400
            # 400 bad session
            response = make_api_request("/model", PUT, authorize_headers(str(uuid.uuid4())),
                                        data={"model_id": model_id}, files={"file": f})
            assert response.status_code == 400
            response = make_api_request("/model", PUT, HEADERS,
                                        params=None)
            assert response.status_code == 400
        finally:
            # clean up
            clear_session_values(session, clear_session=True)
            f.close()

    def test_model_post(self):
        model_id = "my_model"
        session = make_and_unpack_request("/session", GET, HEADERS)
        f = open(TEST_MODEL_FILE, 'rb')
        try:
            # search for, expect missing
            response = make_api_request("/model", GET, authorize_headers(session),
                                        params={"model_id": model_id})
            assert (response.status_code == 404)
            # cached: populate it for our session
            job = None
            response = make_api_request("/model", POST, authorize_headers(session),
                                            data={"model_id": model_id}, files={"file": f})
            assert (response.status_code == 200)

            # Now actually check retrieval
            result = make_and_unpack_request("/model", GET, authorize_headers(session),
                                             params={"model_id": model_id})
            assert (type(result) == dict)
            # 400 No session
            response = make_api_request("/model", POST, HEADERS,
                                        data={"model_id": model_id}, files={"file": f})
            assert response.status_code == 400
            # 400 bad session
            response = make_api_request("/model", POST, authorize_headers(str(uuid.uuid4())),
                                        data={"model_id": model_id}, files={"file": f})
            assert response.status_code == 400
            response = make_api_request("/model", POST, HEADERS,
                                        params=None)
            assert response.status_code == 400
        finally:
            # clean up
            clear_session_values(session, clear_session=True)
            f.close()

    def test_model_list(self):
        model_id = "my_model"
        session = make_and_unpack_request("/session", GET, HEADERS)
        try:
            # search for, expect missing
            result = make_and_unpack_request("/model/list", GET, authorize_headers(session))
            assert (type(result) == list and len(result) == 0)
            # cached: populate it for our session
            with open(TEST_MODEL_FILE, 'rb') as f:
                response = make_api_request("/model", PUT, authorize_headers(session),
                                            data={"model_id": model_id}, files={"file": f})
            assert (response.status_code == 200)

            # Now actually check retrieval
            result = make_and_unpack_request("/model/list", GET, authorize_headers(session))
            assert (type(result) == list and len(result) == 1)
            # 400 No session
            response = make_api_request("/model/list", GET, HEADERS)
            assert response.status_code == 400
            # 400 bad session
            response = make_api_request("/model/list", GET, authorize_headers(str(uuid.uuid4())))
            assert response.status_code == 400
        finally:
            # clean up
            clear_session_values(session, clear_session=True)

    def test_model_gapfill(self):
        model_id = "my_model"
        session = make_and_unpack_request("/session", GET, HEADERS)
        try:
            with open(TEST_MODEL_FILE, 'rb') as f:
                response = make_api_request("/model", PUT, authorize_headers(session),
                                            data={"model_id": model_id}, files={"file": f})
            assert (response.status_code == 200)

            # cached
            job = make_and_unpack_request("/probanno/calculate", GET, authorize_headers(session),
                                          params={"fasta_id": CACHED_FASTA})
            assert job['sid'] == session
            assert job['job'] == CALCULATE_PROBANNO_JOB
            assert job['target'] == CACHED_FASTA
            assert job['status'] == COMPLETE

            # Now actually check gap-filling
            job = make_and_unpack_request("/model/gapfill", GET, authorize_headers(session),
                                             params={"model_id": model_id,
                                                     "fasta_id": CACHED_FASTA,
                                                     "output_id": "my_new_model",
                                                     "template": "GramNegative"})
            assert job['sid'] == session
            assert job['job'] == GAPFILL_MODEL_JOB
            assert job['target'] == model_id

            # 400 No session
            response = make_api_request("/model/gapfill", GET, HEADERS,
                                        params={"model_id": model_id})
            assert response.status_code == 400
            # 400 bad session
            response = make_api_request("/model/gapfill", GET, authorize_headers(str(uuid.uuid4())),
                                        params={"model_id": model_id})
            assert response.status_code == 400
            response = make_api_request("/model/gapfill", GET, HEADERS,
                                        params=None)
            assert response.status_code == 400
            response = make_api_request("/model/gapfill", GET, authorize_headers(session),
                                        params={"model_id": model_id,
                                                 "fasta_id": NOT_A_FASTA,
                                                 "output_id": "my_new_model",
                                                 "template": "GramNegative"})
            assert response.status_code == 404
            response = make_api_request("/model/gapfill", GET, authorize_headers(session),
                                        params={"model_id": NOT_A_FASTA,
                                                "fasta_id": CACHED_FASTA,
                                                "output_id": "my_new_model",
                                                "template": "GramNegative"})
            assert response.status_code == 404
            # Test missing arguments
            response = make_api_request("/model/gapfill", GET, authorize_headers(session),
                                        params={"model_id": NOT_A_FASTA,
                                                "fasta_id": CACHED_FASTA,
                                                "template": "GramNegative"})
            assert response.status_code == 400
            response = make_api_request("/model/gapfill", GET, authorize_headers(session),
                                        params={"model_id": NOT_A_FASTA,
                                                "output_id": "my_new_model",
                                                "template": "GramNegative"})
            assert response.status_code == 400
            response = make_api_request("/model/gapfill", GET, authorize_headers(session),
                                        params={"fasta_id": CACHED_FASTA,
                                                "output_id": "my_new_model",
                                                "template": "GramNegative"})
            assert response.status_code == 400
        finally:
            # clean up
            clear_session_values(session, clear_session=True)


class TestJobMethods(unittest.TestCase):

    def test_get_job(self):
        session = make_and_unpack_request("/session", GET, HEADERS)
        try:
            response = make_api_request("/job", GET, authorize_headers(session),
                                        params={"job_id": FASTA_1})
            assert response.status_code == 404
            job = make_and_unpack_request("/probanno/calculate", GET, authorize_headers(session),
                                          params={"fasta_id": FASTA_1})
            assert job['sid'] == session
            assert job['job'] == CALCULATE_PROBANNO_JOB
            assert job['target'] == FASTA_1
            job = make_and_unpack_request("/job", GET, authorize_headers(session),
                                          params={"job_id": job['jid']})
            assert job['sid'] == session
            assert job['job'] == CALCULATE_PROBANNO_JOB
            assert job['target'] == FASTA_1
            # 404 JOB not found
            response = make_api_request("/job", GET, authorize_headers(session),
                                        params={"job_id": NOT_A_FASTA})
            assert response.status_code == 404
            # 400 No session
            response = make_api_request("/job", GET, HEADERS,
                                        params={"job_id": job['jid']})
            # 400 bad session
            response = make_api_request("/job", GET, authorize_headers(str(uuid.uuid4())),
                                        params={"job_id": job['jid']})
            assert response.status_code == 400
        finally:
            # clean up
            clear_session_values(session, clear_session=True)

    def test_list_job(self):
        session = make_and_unpack_request("/session", GET, HEADERS)
        try:
            result = make_and_unpack_request("/job/list", GET, authorize_headers(session))
            assert type(result) == list and len(result) == 0
            job = make_and_unpack_request("/probanno/calculate", GET, authorize_headers(session),
                                          params={"fasta_id": FASTA_1})
            assert job['sid'] == session
            assert job['job'] == CALCULATE_PROBANNO_JOB
            assert job['target'] == FASTA_1
            result = make_and_unpack_request("/job/list", GET, authorize_headers(session))
            assert type(result) == list and len(result) == 1
            # 400 No session
            response = make_api_request("/job/list", GET, HEADERS)
            # 400 bad session
            response = make_api_request("/job/list", GET, authorize_headers(str(uuid.uuid4())))
            assert response.status_code == 400
        finally:
            # clean up
            clear_session_values(session, clear_session=True)

def make_api_request(path, method, headers, params=None, files=None, data=None):
    """
    helper method for making a request and unpacking the JSON result
    :param path: sub path of the API
    :param method: HTTP method
    :param headers: Associated headers
    :return: HTTP result
    """
    response = requests.request(method, BASE_URL + path, headers=headers, params=params, files=files, data=data)
    return response


def make_and_unpack_request(path, method, headers, params=None, files=None, data=None):
    """
       helper method for making a request and unpacking the JSON result
       :param path: sub path of the API
       :param method: HTTP method
       :param headers: Associated headers
       :return: HTTP result
       """
    response = make_api_request(path, method, headers, params=params, files=files, data=data)
    return json.loads(response.text)


def authorize_headers(session):
    auth_headers = {"session_id": session}
    auth_headers.update(HEADERS)
    return auth_headers


def clear_session_values(session, clear_session=False):
    make_and_unpack_request('/session/clear', GET, authorize_headers(session), params={'clear_session': clear_session})


if __name__ == '__main__':
    unittest.main()

