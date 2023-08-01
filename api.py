""""
# Eduka Project Web Tunnel

This tunnel allowed anyone with the right api key to execute services from a web browser.
"""

import os
import sys

sys.path.append('.')

print(sys.path)

import subprocess
from flask import Flask, request, send_file
from dotenv import load_dotenv
from setup_logger import logger


load_dotenv()

app = Flask(__name__)
app.config['TRAP_HTTP_EXCEPTIONS'] = True
key = os.environ.get("api_key")
service_dirs = "eduka_projects/services"

msg400 = {
    'code': 400,
    'state': 'error',
    'msg': "The server cannot or will not process the request due to an apparent client error. Please check the instruction command"
}
msg401 = {
    'code': 401,
    'state': 'error',
    'msg': "invalid authentication credentials for the requested resource."
}

msg404 = {
    'code': 404,
    'state': 'error',
    'msg': "The requested URL was not found on the server."
}
msg500 = {
    'code': 500,
    'state': 'error',
    'msg': "Internal server error"
}

msg200 = {
    'code': 200,
    'state': 'Success',
    'msg': "Authorized"
}

msg201 = {
    'code': 201,
    'state': 'Success',
    'msg': "Sub Service  sub_serv  of service_name  has been successfuly executed. A mail with be sent when execution terminates"
}

notif = {
    400: msg400,
    401: msg401,
    404: msg404,
    500: msg500,
    200: msg200,
    201: msg201
}


def auth(key, api_key):
    if key != api_key:
        return notif[401], 401
    return notif[200], 200


@app.errorhandler(404)
# inbuilt function which takes error as parameter
def page_not_found(e):
    api_key = request.args.get("api_key")
    result, code = auth(key, api_key)
    if code == 401:
        return result, 401

    return notif[404], 404


@app.errorhandler(500)
# inbuilt function which takes error as parameter
def internal_server_error(e):
    api_key = request.args.get("api_key")
    result, code = auth(key, api_key)
    if code == 401:
        return result, 401

    return notif[500], 500


@app.route("/")
def hello():
    result, code = auth(key, request.args.get("api_key"))
    if code == 401:
        return result, 401
    return {"Greetings": "Welcome to Enko Education (EDUKA PROJECTS) Web executable"}


@app.route("/service/<module>/<service>")
def sub_service(module, service):
    py_service = service + ".py"
    result, code = auth(key, request.args.get("api_key"))
    if code == 401:
        return result, 401

    _service_dirs = os.listdir(service_dirs)

    if module in _service_dirs:
        module_dir_path = os.path.join(service_dirs, module)
        print(os.listdir(module_dir_path))

        if py_service in os.listdir(module_dir_path):
            from main import launch
            try:
                print("Launching ", service)
                launch(service)
            except Exception as e:
                return [str(e)], 500

            notif[201]['msg'] = notif[201]['msg'].replace(
                "sub_serv",
                " ".join(service.split("_")).capitalize()).replace("service_name", module)

            # Waiting for process to finish
            # streamdata = child.communicate()[0]
            # rc = child.returncode
            # print("OK OK", rc)

            return notif[201], 201

    return notif[400], 400


@app.route("/list-endpoints")
def list_web_endpoints():
    uri = []
    try:
        result, code = auth(key, request.args.get("api_key"))
        if code == 401:
            return result, 401

        for module in os.listdir(service_dirs):
            _path = module
            module_dir = os.path.join(service_dirs, module)
            if os.path.isdir(module_dir):
                for l_service in os.listdir(module_dir):
                    if l_service.endswith("py") and "__" not in l_service:
                        uri.append("/service/" + os.path.join(module, l_service.split(".")[0]) + "?api_key=")
        uri = {
            "code": 201,
            "endpoints": uri
        }
    except Exception as e:
        print(str(e))
        logger.critical("API Exception occured", exc_info=True)
        uri = notif[500]
    finally:
        return uri


@app.route("/file/<file_name>")
def files(file_name):
    # print(auth(key, request.args.get("api_key")))
    # result, code = auth(key, request.args.get("api_key"))
    # if code == 401:
    #     return result, 401

    file_path = f"/home/{os.environ.get('linux_user')}/ftp/files/{file_name}"

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return {"error": 404,
                "msg": f"File {file_name} does not exists. Please check the file name and retry or contact admin."}


@app.route("/assets/<file_name>")
def assets(file_name):
    # print(auth(key, request.args.get("api_key")))
    # result, code = auth(key, request.args.get("api_key"))
    # if code == 401:
    #     return result, 401

    if os.path.exists(file_name):
        return send_file(file_name, as_attachment=True)
    else:
        return {"error": 404,
                "msg": f"File {file_name} does not exists. Please check the file name and retry or contact admin."}


if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0')
    except Exception as e:
        logger.critical("API Exception occured", exc_info=True)
        print(str(e))
