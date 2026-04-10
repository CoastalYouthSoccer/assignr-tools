from os import environ
from sys import (argv, exit, stdout)
import logging
from dotenv import load_dotenv
from getopt import (getopt, GetoptError)
from datetime import (datetime, timedelta)

from assignr.assignr import Assignr
from helpers.helpers import (get_environment_vars, get_spreadsheet_vars,
                             get_coach_information, get_email_vars,
                             create_message, get_assignor_information)
from helpers.email import EMailClient
from helpers import constants

START_DATE = "start_date"
END_DATE = "end_date"

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
        START_DATE: None, END_DATE: None
    }

    rc = 0
    USAGE='USAGE: game_report.py -s <start-date> -e <end-date>' \
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

def process_administrator(email_vars, start_date, end_date, admin_reports,
                          team_rosters, lanyards, borrowed_players):
    subject = f'Administrator Game Reports: {start_date.strftime("%m/%d/%Y")}' \
             f' - {end_date.strftime("%m/%d/%Y")}'
    temp_addresses = [email_vars[constants.ADMIN_EMAIL]]
    email_addresses = ','.join(temp_addresses) 

    content = {
        START_DATE: start_date,
        END_DATE: end_date,
        'admin_reports': admin_reports,
        'team_rosters': team_rosters,
        'lanyards': lanyards,
        'borrowed_players': borrowed_players
    }

    message = create_message(content, 'administrator.html.jinja')

    response = send_email(email_vars, subject, message,
                          email_addresses)
    if response:
        logger.error(response)

    logger.info("Completed Administrator Report")

def process_misconducts(email_vars, misconducts, start_date,
                        end_date, assignor_emails):
    temp_emails = [email_vars[constants.MISCONDUCTS_EMAIL]]
    temp_emails.extend(assignor_emails)
    email_addresses = ",".join(temp_emails)

    subject = f'Misconduct: {start_date.strftime("%m/%d/%Y")}' \
             f' - {end_date.strftime("%m/%d/%Y")}'
    content = {
        START_DATE: start_date,
        END_DATE: end_date,
        'misconducts': misconducts
    }

    message = create_message(content, 'misconduct.html.jinja')

    response = send_email(email_vars, subject, message,
                          email_addresses)

    if response:
        logger.error(response)

    logger.info("Completed Misconduct Report")

def process_assignor_reports(email_vars, reports, start_date, end_date,
                             assignors):
    subject = f'Game Reports Needing Attention: {start_date.strftime("%m/%d/%Y")}' \
             f' - {end_date.strftime("%m/%d/%Y")}'

    for report in reports:
        content = {
            START_DATE: start_date,
            END_DATE: end_date,
            'report': report
        }

        message = create_message(content, 'assignor.html.jinja')

        temp_emails = []
        for assignor in assignors[report['league']]:
            temp_emails.append(assignor['email'])
        assignor_emails = ','.join(temp_emails)

        response = send_email(email_vars, subject, message,
                              assignor_emails)
    
        if response:
            logger.error(response)

    logger.info("Completed Assignors Report")

def main():
    logger.info("Starting Game Report")
    rc, args = get_arguments(argv[1:])
    if rc:
        exit(rc)

    rc, env_vars = get_environment_vars()
    if rc:
        exit(rc)

    rc, spreadsheet_vars = get_spreadsheet_vars()
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

    coaches = get_coach_information(spreadsheet_vars[constants.SPREADSHEET_ID],
                                    spreadsheet_vars[constants.SPREADSHEET_RANGE])
    
    assignors = get_assignor_information()
    assignor_emails = []
    for association in assignors:
        for assignor in assignors[association]:
            assignor_emails.append(assignor['email'])

    reports = assignr.get_reports(args[START_DATE],
                                    args[END_DATE],
                                    assignors,
                                    coaches)
    process_misconducts(email_vars, reports['misconducts'],
                        args[START_DATE], args[END_DATE],
                        assignor_emails)
    process_administrator(email_vars, args[START_DATE], args[END_DATE],
                          reports['admin_reports'], reports['team_rosters'],
                          reports['lanyards'], reports['borrowed_players'])
    process_assignor_reports(email_vars, reports['assignor_reports'],
                             args[START_DATE], args[END_DATE],
                             assignors)
    logger.info("Completes Game Report")

if __name__ == "__main__":
    main()
