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

try:
    import logging
    import sys
    import getopt
    from bootstrap import *
    from bootstrap import service
    import concurrent.futures
    from services.code_manager import get_good_codes_from_excel


    # Read command arguments
    argv = sys.argv[1:]
    cmd = ""
    options, args = getopt.getopt(argv, "s:", ["service ="])
    for name, value in options:
        if name.strip() == '-s' or name.strip() == '--service':
            cmd = value

    schools = parameters['enko_education']['schools'].keys()

    """
    Main dispatcher thread pool executor
    """
    if cmd in service.load:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(service.load[cmd].run, schools, [cmd])

except Exception as e:
    print("Program launch error", str(e))
    logging.critical("Program launch error", exc_info=True)
