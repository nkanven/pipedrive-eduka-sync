"""
# Eduka Projects V1

This project aims to consolidate all **Enko Education** microservices around a main service manager
for an easy code base update and scalability in mind.

## Comprehension / Recommendations

**Eduka Projects** is a basket of service manager via a main unit also acting as the entry point
For each new microservice, the developer should:
    1. create the service module in ***eduka-projects.services*** package.
    2. initialize a ***service_name*** in the ***new_module.__init__.py***
    3. register that service on the *dispatcher* method situated at ***eduka-projects.service.dispatch***.
        The key name should be the command line parameter for the service. E.g if you intend to execute
        backup_automation, the command line you run is ````python main.py -s backup_automation```. The dispatcher will
        handle the rest.

For the code base stability and integrity to prevail, developer need to respect this minimal recommendations
"""
import os
# TODO: Convert KeyError in mail class and check api and all the code base

import time
import datetime

import sys
import getopt
from eduka_projects.services.dispatch import dispatcher
from eduka_projects.utils.eduka_exceptions import EdukaMailServiceKeyError
import concurrent.futures
from eduka_projects.utils.mail import EnkoMail
from eduka_projects.bootstrap import Bootstrap

start_time = time.time()
bts = Bootstrap()

weborder = lambda service_name: os.path.join("eduka_projects/weborders", service_name)


def launch(command):
    if os.path.exists(weborder(command)):
        os.remove(weborder(command))
    try:
        schools = bts.parameters['enko_education']['schools'].keys()
        # schools: list = ['enko_mozambique']
        #
        """
        Main dispatcher thread pool executor
        """

        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " Eduka Projects Services Started...")

        # for school in schools:
        #     if school == "enko_cotedivoire":
        #         try:
        #             print("Work started for", school)
        #             dispatcher(command, school)
        #             # Make space between workers execution
        #             # time.sleep(200)
        #         except Exception as e:
        #             print("Exception occured while running " + school + " " + command, str(e))
        #             bts.error_logger.critical("Exception occured while running " + school + " " + command, exc_info=True)

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            for school in schools:
                print("Work started for", school)
                executor.submit(dispatcher, command, school)
                # Make space between workers execution
                time.sleep(3)

        print("Thread work done...")

        # From all schools, get unique emails
        emails = []
        for school in schools:
            for email in bts.parameters['enko_education']['schools'][school]["comma_seperated_emails"].split(","):
                emails.append(email.strip(" "))

        # Add extra emails for login statistics
        # if command == "login":
        #     for email in bts.parameters["global"]["login_stat_recipients"].split(","):
        #         emails.append(email.strip(" "))

        # Only keep unique emails
        unique_emails = set(emails)

        enko_mail = EnkoMail(command, school)
        enko_mail.set_email_cc_list(list(unique_emails))
        enko_mail.mail_builder_selector()
    except EdukaMailServiceKeyError:
        bts.error_logger.critical("Eduka  Mail Service error", exc_info=True)
    except Exception as e:
        print("Program launch error", str(e))
        bts.error_logger.critical("Program launch error", exc_info=True)
    finally:
        end_time = time.time()
        total_time = end_time - start_time
        time_format = str(datetime.timedelta(seconds=total_time))
        print(f"Program took {time_format} to run")


if __name__ == "__main__":
    # Read command arguments
    argv = sys.argv[1:]
    print(argv)
    cmd = ""
    options, args = getopt.getopt(argv, "s:", ["service ="])
    for name, value in options:
        print(name, value)
        if name.strip() == '-s' or name.strip() == '--service':
            if value == "weblaunch":
                cmd = os.listdir("eduka_projects/weborders")[0]
            else:
                cmd = value

    launch(cmd)
