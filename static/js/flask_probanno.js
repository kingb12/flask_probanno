/**
 * Created by bking on 3/1/17.
 */

// ============== STRING CONSTANTS (e.g. root URL, API links, etc.) ====================================================

const ROOT_URL = "http://localhost:5000";
const LIST_MODELS_ENDPOINT = "/api/list/model";
const LIST_PROBANNOS_ENDPOINT = "/api/list/probanno";
const GAPFILL_MODEL_ENDPOINT = "/gapfillmodel";
const DOWNLOAD_PROBANNO_ENDPOINT = "/api/io/downloadprobanno";
const DOWNLOAD_MODEL_ENDPOINT = "/api/io/downloadmodel";
const CHECK_JOB_ENDPOINT = "/api/job/checkjob";

// =====================================================================================================================
function populateTable(table_tbody_id, data) {
    //Retrieve HTML Table element.
    var tbody = document.getElementById(table_tbody_id);
    //Get the count of columns.
    var columnCount = data[0].length;

    //Add the data rows.
    for (var i = 0; i < data.length; i++) {
        row = tbody.insertRow(-1);
        for (var j = 0; j < columnCount; j++) {
            var cell = row.insertCell(-1);
            cell.innerHTML = data[i][j];
            cell.setAttribute("align", "center");
            cell.setAttribute("valign", "center");
        }
    }
    $(document).ready(function() {
        $('#example').DataTable( {
        "scrollY":        "200px",
        "scrollCollapse": true,
        "paging":         false
        } );
    } );
}
function listModels(table_tbody_id) {
    var args = {};
    args.table_tbody_id = table_tbody_id;
    var data = getJsonFromRequest('GET', ROOT_URL + LIST_MODELS_ENDPOINT + "?sid=" + getCookie('session_id'), onResponse, args);
    //process the results into what we actually want to list

    function onResponse(args) {
        var tableArray = [];
        for (i = 0; i < args.data.length; i++) {
            var gapfill_url = ROOT_URL + GAPFILL_MODEL_ENDPOINT + "?model_id=" + args.data[i];
            tableArray.push([args.data[i], '<form action=' + gapfill_url + '><b><input type="submit" value="Gapfill This Model" /></b></form>']);
        }
        populateTable(args.table_tbody_id, tableArray);
    }

}

function listProbannos(table_tbody_id) {
    var args = {};
    args.table_tbody_id = table_tbody_id;
    var data = getJsonFromRequest('GET', ROOT_URL + LIST_PROBANNOS_ENDPOINT, onResponse, args);
    //process the results into what we actually want to list

    function onResponse(args) {
        var tableArray = [];
        for (i = 0; i < args.data.length; i++) {
            var download_url = ROOT_URL + DOWNLOAD_PROBANNO_ENDPOINT;
            tableArray.push([args.data[i],
                '<form method = "get" action=' + download_url + '>' +
                    '<input name="fasta_id" type="hidden" value=' + args.data[i] + ' />' +
                    '<b><input type="submit" value="Download"/></b></form>']);
        }
        populateTable(args.table_tbody_id, tableArray);
    }

}

function getJsonFromRequest(method, url, onResponse, args) {
    // Inspired/copied from: https://www.kirupa.com/html5/making_http_requests_js.htm
    var xhr = new XMLHttpRequest();

    xhr.open(method, url, true);
    xhr.send(null);
    xhr.onreadystatechange = processRequest;


    //readyState == 4 b/c of HTTP Protocol details. This method essentially gets called 5 times
    function processRequest() {
        if (xhr.readyState == 4 && xhr.status === 200) {
            args.data = JSON.parse(xhr.responseText);
            console.log(xhr.responseText);
            onResponse(args);
        }
    }

}

function populateSelect(selectBody, data) {
   //Retrieve HTML Table element.
    var sbody = document.getElementById(selectBody);
    var s = '';
    for (i = 0; i < data.length; i++) {
           s += data[i]
    }
    sbody.innerHTML = s;
}

function selectModels(selectBody) {
    var args = {};
    args.selectBody = selectBody;
    var data = getJsonFromRequest('GET', ROOT_URL + LIST_MODELS_ENDPOINT + "?sid=" + getCookie('session_id'), onResponse, args);
    //process the results into what we actually want to list

    function onResponse(args) {
        var tableArray = [];
        for (i = 0; i < args.data.length; i++) {
            var selectString = '';
            if (getParameterByName('model_id') == args.data[i]) {
                selectString = 'selected="selected"';
            }
            tableArray.push('<option value="' + args.data[i] + '" ' + selectString + ' >' + args.data[i] + '</option>');
        }
        populateSelect(args.selectBody, tableArray);
    }
}

function selectProbannos(selectBody) {
    var args = {};
    args.selectBody = selectBody;
    var data = getJsonFromRequest('GET', ROOT_URL + LIST_PROBANNOS_ENDPOINT, onResponse, args);
    //process the results into what we actually want to list

    function onResponse(args) {
        var tableArray = [];
        for (i = 0; i < args.data.length; i++) {
            var selectString = '';
            if (getParameterByName('probanno_id') == args.data[i]) {
                selectString = 'selected="selected"';
            }
            tableArray.push('<option value="'+ args.data[i] + '" ' + selectString + ' >' + args.data[i] + '</option>');
        }
        populateSelect(args.selectBody, tableArray);
    }
}

function getCookie(name) {
  var value = "; " + document.cookie;
  var parts = value.split("; " + name + "=");
  if (parts.length == 2) return parts.pop().split(";").shift();
}

function getParameterByName(name, url) {
    if (!url) {
      url = window.location.href;
    }
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

function checkJob(jobStatus, job_id) {
    var args = {};
    args.jobStatus = jobStatus;
    var data = getJsonFromRequest('GET', ROOT_URL + CHECK_JOB_ENDPOINT + '?job_id=' + job_id, onResponse, args);

    function onResponse(args) {
        var status = document.getElementById(args.jobStatus);
        status.innerHTML = "<b>" + args.data + "</b>";
        document.job_status = args.data;
    }
}