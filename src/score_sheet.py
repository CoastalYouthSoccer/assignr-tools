from os import environ
from sys import (argv, exit, stdout)
import logging
import csv
from dotenv import load_dotenv
from getopt import (getopt, GetoptError)
from datetime import datetime
from assignr.assignr import Assignr
from helpers.helpers import get_environment_vars

load_dotenv()

log_level = environ.get('LOG_LEVEL', 30)
logging.basicConfig(stream=stdout,
                    level=int(log_level))
logger = logging.getLogger(__name__)

def get_arguments(args):
    arguments = {
        'start_date': None, 'end_date': None, 
        'game_type': None
    }

    rc = 0
    USAGE='USAGE: score_sheet.py -s <start-date> (MM/DD/YYYY) '\
        '-e <end-date> (MM/DD/YYYY) -g <game type, default "Futsal">' 
    try:
        opts, args = getopt(args,"hs:e:g:",
                            ["start-date=","end-date=",
                             "game-type="])
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
        elif opt in ("-g", "--game-type"):
            arguments['game_type'] = arg
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

    if arguments['game_type'] is None:
        arguments['game_type'] = 'Futsal'
        logger.info('Game Type not provided, defaulting to "Futsal"')

    return rc, arguments


def main():
    rc, args = get_arguments(argv[1:])
    if rc:
        exit(rc)

    rc, env_vars = get_environment_vars()
    if rc:
        exit(rc)

    assignr = Assignr(env_vars['CLIENT_ID'], env_vars['CLIENT_SECRET'],
                      env_vars['CLIENT_SCOPE'], env_vars['BASE_URL'],
                      env_vars['AUTH_URL'])

    games = assignr.get_league_games(args['game_type'], args['start_date'],
                                     args['end_date'])
    print(games)

if __name__ == "__main__":
    main()
