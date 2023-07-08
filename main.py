"""
# Eduka Projects V1

This project aims to consolidate all **Enko Education** microservices around a main service manager
for an easy code base update and scalability in mind.

## Comprehension / Recommendations

**Eduka Projects** is a basket of service manager via a main unit also acting as the entry point
For each new microservice, the developer should:
    1. create the service module in ***eduka-projects.services*** package.
    2. initialize a ***service_name*** in the ***new_module.__init__.py***
    3. register that service on the *load* Dict situated at ***eduka-projects.bootstrap.service***.
        The key name should be the command line parameter for the service. E.g if you intend to execute
        database_backup, the command line you run is ````python main.py -s database_backup``` which associated
        with its method **backup** on ***eduka-projects.bootstrap.service***

For the code base stability and integrity to prevail, developer need to respect this minimal recommendations
"""

import time

try:
    import logging
    import sys
    import getopt
    from bootstrap import parameters
    from bootstrap import service
    import concurrent.futures
    from services.code_manager import get_good_codes_from_excel
    from utils.rialization import deserialize
    from utils.mail import EnkoMail

    # Read command arguments
    argv = sys.argv[1:]
    cmd = ""
    options, args = getopt.getopt(argv, "s:", ["service ="])
    for name, value in options:
        if name.strip() == '-s' or name.strip() == '--service':
            cmd = value

    schools = parameters['enko_education']['schools'].keys()
    #schools:list = ['enko_mali']
    """
    Main dispatcher thread pool executor
    """
    if cmd in service.load:

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            for school in schools:
                executor.submit(service.load[cmd]["loader"].run, school, cmd)
                # Make space between workers execution
                time.sleep(5)
                print("Work started for", school)
        print("Thread work done...")

        # From all schools, get unique emails
        emails = []
        for school in schools:
            for email in parameters['enko_education']['schools'][school]["comma_seperated_emails"].split(","):
                emails.append(email.strip(" "))

        unique_emails = set(emails)

        enko_mail = EnkoMail(cmd, school, parameters)
        enko_mail.set_email_cc_list(list(unique_emails))
        enko_mail.mail_summarized()
        enko_mail.send_mail()
except Exception as e:
    print("Program launch error", str(e))
    logging.critical("Program launch error", exc_info=True)
