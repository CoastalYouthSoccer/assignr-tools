from os import environ
from sys import (argv, exit, stdout)
import logging
import csv
from dotenv import load_dotenv
from getopt import (getopt, GetoptError)
from datetime import datetime

from helpers.helpers import check_environment_vars
from assignr.assignr import Assignr

load_dotenv()

logger = logging.getLogger(__name__)

def get_arguments(args):
    arguments = {
        'start_date': None, 'end_date': None
    }

    rc = 0
    USAGE='USAGE: misconduct.py -s <start-date> -e <end-date>' \
    ' DATE FORMAT=MM/DD/YYYY'

    try:
        opts, args = getopt(args,"hs:e:",
                            ["start-date=","end-date="])
    except GetoptError:
        logger.error(USAGE)
        return 77, arguments

    for opt, arg in opts:
        if opt == '-h':
            logger.error(USAGE)
            return 99, arguments
        elif opt in ("-s", "--start-date"):
            arguments['start_date'] = arg
        elif opt in ("-e", "--end-date"):
            arguments['end_date'] = arg

    if arguments['start_date'] is None or arguments['end_date'] is None:
        logger.error(USAGE)
        return 99, arguments

    try:
         arguments['start_date'] = datetime.strptime(arguments['start_date'], "%m/%d/%Y").date()
    except ValueError:
        logger.error(f"Start Date value, {arguments['start_date']} is invalid")
        rc = 88
    try:
         arguments['end_date'] = datetime.strptime(arguments['end_date'], "%m/%d/%Y").date()
    except ValueError:
        logger.error(f"End Date value, {arguments['end_date']} is invalid")
        rc = 88

    return rc, arguments

def main():
    log_level = environ.get('LOG_LEVEL', 'INFO')
    logging.basicConfig(stream=stdout,
                        level=int(log_level))

    rc, args = get_arguments(argv[1:])
    if rc:
        exit(rc)

    errors, env_vars = check_environment_vars()
    if errors:
        for error in errors:
            logger.error(error)
        exit(88)

    assignr = Assignr(env_vars['CLIENT_ID'], env_vars['CLIENT_SECRET'],
                      env_vars['CLIENT_SCOPE'], env_vars['BASE_URL'],
                      env_vars['AUTH_URL'])
    
    misconducts = assignr.get_misconducts(args['start_date'],
                                           args['end_date'])


if __name__ == "__main__":
    main()
