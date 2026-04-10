from os import environ
from sys import (argv, exit, stdout)
import logging
from dotenv import load_dotenv
from getopt import (getopt, GetoptError)
from datetime import (datetime, timedelta)

from assignr.assignr import Assignr
from helpers.helpers import (get_environment_vars, get_email_vars,
                             create_message, get_center_referee_info,
                             get_assignor_information)
from helpers.email import EMailClient
from helpers import constants

START_DATE = "start_date"
END_DATE = "end_date"
REFEREE_REMINDER = "referee_reminder"

env_file = environ.get('ENV_FILE', '.env')
load_dotenv(env_file)

log_level = environ.get('LOG_LEVEL', logging.INFO)
logging.basicConfig(stream=stdout,
                    format='%(asctime)s %(levelname)s %(message)s',
                    level=int(log_level),
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


def get_arguments(args):
    arguments = {
        START_DATE: None, END_DATE: None, REFEREE_REMINDER: False
    }

    rc = 0
    USAGE='USAGE: missing_game_reports.py -s <start-date> -e <end-date>' \
    ' DATE FORMAT=MM/DD/YYYY -r'

    try:
        opts, args = getopt(args,"hrs:e:",
                            ["start-date=","end-date="])
    except GetoptError:
        logger.error(USAGE)
        return 77, arguments

    for opt, arg in opts:
        if opt == '-h':
            logger.error(USAGE)
            return 99, arguments
        elif opt == '-r':
            arguments[REFEREE_REMINDER] = True
        elif opt in ("-s", "--start-date"):
            arguments[START_DATE] = arg
        elif opt in ("-e", "--end-date"):
            arguments[END_DATE] = arg

    try:
        if arguments[END_DATE]:
            arguments[END_DATE] = \
                datetime.strptime(arguments[END_DATE], "%m/%d/%Y").date()
        else:
            arguments[END_DATE] = datetime.now().date()
            logger.info(f"No end date provided, setting to {arguments[END_DATE]}")
        logger.info(f"End Date set to {arguments[END_DATE]}")
    except ValueError:
        logger.error(f"End Date value, {arguments[END_DATE]} is invalid")
        rc = 88

    try:
        if arguments[START_DATE]:
            arguments[START_DATE] = \
                datetime.strptime(arguments[START_DATE], "%m/%d/%Y").date()
        else:
            arguments[START_DATE] = arguments[END_DATE] - \
                timedelta(days=7)
            logger.info(f"No start date provided, setting to {arguments[START_DATE]}")

        logger.info(f"Start Date set to {arguments[START_DATE]}")           
    except ValueError:
        logger.error(f"Start Date value, {arguments[START_DATE]} is invalid")
        rc = 88

    if arguments[START_DATE] > arguments[END_DATE]:
        logger.error(f"Start Date {arguments[START_DATE]} is after End Date {arguments[END_DATE]}")
        rc = 88

    return rc, arguments

def send_email(email_vars, subject, message, send_to):
    email_client = EMailClient(
        email_vars[constants.EMAIL_SERVER], email_vars[constants.EMAIL_PORT],
        email_vars[constants.EMAIL_USERNAME], 'Game Report',
        email_vars[constants.EMAIL_PASSWORD])

    return email_client.send_email(subject, message,
                                   send_to, True)

def send_referee_reminder(game, email_vars, subject):
    center_referee = get_center_referee_info(game['referees'])
    assignor_addresses = game['assignor']['email_addresses']
    email_addresses = ",".join(center_referee['email_addresses'] + assignor_addresses)
    message = create_message(game, 'missing_referee_report.html.jinja')

    response = send_email(email_vars, subject, message,
                          email_addresses)
    if response:
        logger.error(response)
    else:
        logger.info(f"Sent an email to {game['league']}")

def main():
    logger.info("Starting Missing Game Report")
    rc, args = get_arguments(argv[1:])
    if rc:
        exit(rc)

    rc, env_vars = get_environment_vars()
    if rc:
        exit(rc)

    rc, email_vars = get_email_vars()
    if rc:
        exit(rc)

    assignr = Assignr(env_vars[constants.CLIENT_ID],
                      env_vars[constants.CLIENT_SECRET],
                      env_vars[constants.CLIENT_SCOPE],
                      env_vars[constants.BASE_URL],
                      env_vars[constants.AUTH_URL])
    
    assignors = get_assignor_information()
    assignor_emails = []
    for association in assignors:
        for assignor in assignors[association]:
            assignor_emails.append(assignor['email'])

    assignr.load_referees_assignors()

    games = assignr.get_game_ids(args[START_DATE],
                                    args[END_DATE])
    games = assignr.match_games_to_reports(args[START_DATE],
                                    args[END_DATE], games)

    game_reports = []
    subject = f'Game Reports Needing Attention: {args[START_DATE].strftime("%m/%d/%Y")}' \
             f' - {args[END_DATE].strftime("%m/%d/%Y")}'

    for game in games.values():
        if not game['cancelled'] and (game['game_report_url'] is None or \
            not game['home_roster'] or not game['away_roster']): 
            game_reports.append(game)
            if args[REFEREE_REMINDER]:
                send_referee_reminder(game, email_vars, subject)

    content = {'reports': game_reports}
    message = create_message(content, 'missing_report.html.jinja')

    response = send_email(email_vars, subject, message,
                          email_vars[constants.ADMIN_EMAIL])
    if response:
        logger.error(response)
    logger.info("Completed Missing Game Report")

if __name__ == "__main__":
    main()
