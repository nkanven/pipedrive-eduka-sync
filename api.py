""""
# Eduka Project Web Tunnel

This tunnel allowed anyone with the right api key to execute services from a web browser.
"""

import os
import subprocess
from flask import Flask, request

app = Flask(__name__)
app.config['TRAP_HTTP_EXCEPTIONS'] = True
key = "XNSS-HSJW-3NGU-8XTJ"

msg = {
    'code': 404,
    'state': 'error',
    'msg': "The requested URL was not found on the server."
}


@app.errorhandler(404)
# inbuilt function which takes error as parameter
def page_not_found(e):
    return msg, 404

@app.errorhandler(500)
# inbuilt function which takes error as parameter
def page_not_found(e):
    msg['code'] = 500
    msg['msg'] = "Internal server error"
    return msg, 500


@app.route("/")
def hello():
    return {"Greetings":"Welcome to Enko Education (EDUKA PROJECTS) Web executable"}


@app.route("/service/<service_name>")
def service(service_name):
    api_key = request.args.get("api_key")

    if key != api_key:
        msg['code'] = 401
        msg['state'] = 'Rejected'
        msg['msg'] = "You are not authorized to access this resource"
        return msg, 401

    if service_name in os.listdir("services"):
        #os.system("source venv/bin/activate && python main.py -s " + service_name)
        python_venv = os.getcwd() + os.sep + "venv/bin/python"
        child = subprocess.Popen([python_venv, 'main.py', '-s', service_name], subprocess.PIPE)
        msg['code'] = 201
        msg['state'] = 'Success'
        msg['msg'] = "Service " + service_name + " has been successfuly executed. " \
                                                 "A mail with be sent when execution terminates"

        """
        Waiting for process to finish
        streamdata = child.communicate()[0]
        rc = child.returncode
        print("OK OK", rc)"""

    return msg, 201


@app.route("/service/<service_name>/<sub_serv>")
def sub_service(service_name, sub_serv):
    api_key = request.args.get("api_key")

    if key != api_key:
        msg['code'] = 401
        msg['state'] = 'Rejected'
        msg['msg'] = "You are not authorized to access this resource"
        return msg, 401

    if service_name in os.listdir("services"):
        #os.system("source venv/bin/activate && python main.py -s " + service_name)
        python_venv = os.getcwd() + os.sep + "venv/bin/python"
        child = subprocess.Popen([python_venv, 'main.py', '-s', sub_serv], subprocess.PIPE)
        msg['code'] = 201
        msg['state'] = 'Success'
        msg['msg'] = "Sub Service " + sub_serv + " of " + service_name +" has been successfuly executed. " \
                                                 "A mail with be sent when execution terminates"

        """
        Waiting for process to finish
        streamdata = child.communicate()[0]
        rc = child.returncode
        print("OK OK", rc)"""

    return msg, 201

if __name__ == "__main__":
    app.run(host='0.0.0.0')
