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

    if cmd in service.load:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(service.load[cmd].run, schools, [cmd])

except Exception as e:
    print("Program launch error", str(e))
    logging.critical("Program launch error", exc_info=True)
