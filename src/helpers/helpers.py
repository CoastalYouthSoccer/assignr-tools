from os import (environ, path)
import re

from dateutil import parser
import logging
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import csv
from google import auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from helpers.constants import ADMIN_EMAIL, ADMIN_NARRATIVE, ADMIN_REVIEW, \
    AUTH_URL, ASSIGNOR_CSV_FILE, BASE_URL, CLIENT_ID, CLIENT_SECRET, \
    CLIENT_SCOPE, CREW_CHANGES, EMAIL_PASSWORD, EMAIL_PORT, \
    EMAIL_SERVER, EMAIL_USERNAME, GOOGLE_APPLICATION_CREDENTIALS, \
    MISCONDUCTS_EMAIL, NARRATIVE, NOT_ASSIGNED, SPREADSHEET_ID, \
    SPREADSHEET_RANGE, START_TIME

logger = logging.getLogger(__name__)

def set_boolean_value(value):
    if value is None:
        return False
    return value.lower() in ['true', '1', 't', 'y', 'yes']

def format_date_yyyy_mm_dd(date) -> str:
    formatted_date = None
    try:
        formatted_date = date.strftime("%Y-%m-%d")
    except Exception as e:
        logger.error(f"Failed to format date: {date}, error: {e}")
    return formatted_date
    
# Jinja template formatters
def format_str_mm_dd_yyyy(date_str) -> str:
    formatted_date = None
    try:
        dt = parser.parse(date_str)
        formatted_date = dt.strftime("%m/%d/%Y")
    except parser.ParserError:
        logger.error(f"Failed to parse date: {date_str}")
    except parser.UnknownTimezoneWarning:
        logger.error(f"Invalid Time zone: {date_str}")
    except Exception as e:
        logger.error(f"Unknown error: {e}")
    return formatted_date

def format_str_hh_mm(date_str) -> str:
    formatted_time = None
    try:
        dt = parser.parse(date_str)
        formatted_time = dt.strftime("%I:%M %p")
    except parser.ParserError:
        logger.error(f"Failed to parse date: {date_str}")
    except parser.UnknownTimezoneWarning:
        logger.error(f"Invalid Time zone: {date_str}")
    except Exception as e:
        logger.error(f"Unknown error: {e}")
    return formatted_time

def format_date_mm_dd_yyyy(date) -> str:
    formatted_date = None
    try:
        formatted_date = date.strftime("%m/%d/%Y")
    except parser.ParserError:
        logger.error(f"Failed to parse date: {date}")
    except parser.UnknownTimezoneWarning:
        logger.error(f"Invalid Time zone: {date}")
    except Exception as e:
        logger.error(f"Unknown error: {e}")
    return formatted_date

def format_date_hh_mm(date) -> str:
    formatted_time = None
    try:
        formatted_time = date.strftime("%I:%M %p")
    except parser.ParserError:
        logger.error(f"Failed to parse date: {date}")
    except parser.UnknownTimezoneWarning:
        logger.error(f"Invalid Time zone: {date}")
    except Exception as e:
        logger.error(f"Unknown error: {e}")
    return formatted_time

def create_message(content, template_name):
    logger.debug('Starting create message ...')
    message = None
    template_dir = path.join(
            path.dirname(path.realpath(__file__)),
            "templates/")
    jinja_env = Environment(
        autoescape=True,
        loader=FileSystemLoader(template_dir))
    jinja_env.filters['format_mm_dd_yyyy'] = format_date_mm_dd_yyyy
    jinja_env.filters['format_hh_mm'] = format_date_hh_mm
    try:
        template = jinja_env.get_template(template_name)
        message = template.render(content)
    except TemplateNotFound as tf:
        logger.error(f"Missing File: {tf}")

    except Exception as e:
        logger.error(f"Error: {e}")

    logger.debug('Completed create message ...')
    return message

def load_sheet(sheet_id, sheet_range) -> list:
    credentials, _ = auth.default()
    sheet_values = []

    try:
        service = build('sheets', 'v4', credentials=credentials, cache_discovery=False)
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=sheet_id, range=sheet_range).execute()
        sheet_values = result.get('values', [])
        logger.info(f"{len(sheet_values)} rows retrieved")
    except HttpError as error:
        logger.error(f"An error occurred: {error}")
    
    return sheet_values

def rows_to_dict(rows):
    result = {}

    for row in rows:
        current_level = result
        for key in row[:-2]:
            current_level = current_level.setdefault(key, {})
        current_level[row[-2]] = row[-1]

    return result

def get_coach_information(spreadsheet_id, sheet_range) -> dict:
    rows =  []

    temp_values = load_sheet(spreadsheet_id, sheet_range)
    for row in temp_values:
        if row and 'grade' in row[0].lower():
            rows.append(row)

    return rows_to_dict(rows)

def get_assignor_information():
    results = {}

    try:
        with open(environ[ASSIGNOR_CSV_FILE], 'r') as csv_file:
            reader = csv.reader(csv_file)
            for row in reader:
                if row[0] in results:
                    results[row[0]].append({
                        'email': f'{row[2]} {row[1]}<{row[3]}>'
                    })
                else:
                    results[row[0]] = [{
                        'email': f'{row[2]} {row[1]}<{row[3]}>'
                    }]
    except KeyError:
        logger.error(f"{ASSIGNOR_CSV_FILE} environment variable not provided")
        return results
    except FileNotFoundError:
        logger.error(f"{environ[ASSIGNOR_CSV_FILE]} Not Found!")
        return results

    return results

def get_center_referee_info(payload):
    referee = {
        'first_name': None,
        'last_name': None,
        'email_addresses': []
    }

    try:
        for official in payload:
            if official['position'] == 'Referee':
                referee['first_name'] = official['first_name']
                referee['last_name'] = official['last_name']
                referee['email_addresses'] = official['email_addresses']
    except KeyError as ke:
        logging.error(f"Key: {ke}, missing from Get Referee response")
            
    return referee
    
def get_environment_vars():
    rc = 0
    env_vars = {
        CLIENT_SECRET: None,
        CLIENT_ID: None,
        CLIENT_SCOPE: None,
        AUTH_URL: None,
        BASE_URL: None
    }

    try:
        env_vars[CLIENT_SECRET] = environ[CLIENT_SECRET]
    except KeyError:
        logger.error(f'{CLIENT_SECRET} environment variable is missing')
        rc = 66

    try:
        env_vars[CLIENT_ID] = environ[CLIENT_ID]
    except KeyError:
        logger.error(f'{CLIENT_ID} environment variable is missing')
        rc = 66

    try:
        env_vars[CLIENT_SCOPE] = environ[CLIENT_SCOPE]
    except KeyError:
        logger.error(f'{CLIENT_SCOPE} environment variable is missing')
        rc = 66

    try:
        env_vars[AUTH_URL] = environ[AUTH_URL]
    except KeyError:
        logger.error(f'{AUTH_URL} environment variable is missing')
        rc = 66

    try:
        env_vars[BASE_URL] = environ[BASE_URL]
    except KeyError:
        logger.error(f'{BASE_URL} environment variable is missing')
        rc = 66

    return rc, env_vars

def get_spreadsheet_vars():
    rc = 0
    env_vars = {
        SPREADSHEET_ID: None,
        SPREADSHEET_RANGE: None,
        GOOGLE_APPLICATION_CREDENTIALS: None
    }

    try:
        env_vars[GOOGLE_APPLICATION_CREDENTIALS] = \
            environ[GOOGLE_APPLICATION_CREDENTIALS]
    except KeyError:
        logger.error(f'{GOOGLE_APPLICATION_CREDENTIALS} environment variable is missing')
        rc = 55

    try:
        env_vars[SPREADSHEET_ID] = environ[SPREADSHEET_ID]
    except KeyError:
        logger.error(f'{SPREADSHEET_ID} environment variable is missing')
        rc = 55

    try:
        env_vars[SPREADSHEET_RANGE] = environ[SPREADSHEET_RANGE]
    except KeyError:
        logger.error(f'{SPREADSHEET_RANGE} environment variable is missing')
        rc = 55

    return rc, env_vars

def get_email_vars():
    rc = 0
    env_vars = {
        EMAIL_SERVER: 'smtp.gmail.com',
        EMAIL_PORT: 587,
        EMAIL_USERNAME: None,
        EMAIL_PASSWORD: None,
        ADMIN_EMAIL: None,
        MISCONDUCTS_EMAIL: None
    }

    try:
        env_vars[EMAIL_SERVER] = environ[EMAIL_SERVER]
    except KeyError:
        logger.info(f'{EMAIL_SERVER} environment variable is missing, defaulting to "smtp.gmail.com"')

    try:
        env_vars[EMAIL_PORT] = int(environ[EMAIL_PORT])
    except KeyError:
        logger.info(f'{EMAIL_PORT} environment variable is missing, defaulting to 587')
    except ValueError:
        logger.error(f'{EMAIL_PORT} environment variable is not an integer')
        rc = 55

    try:
        env_vars[EMAIL_USERNAME] = environ[EMAIL_USERNAME]
    except KeyError:
        logger.error(f'{EMAIL_USERNAME} environment variable is missing')
        rc = 55

    try:
        env_vars[EMAIL_PASSWORD] = environ[EMAIL_PASSWORD]
    except KeyError:
        logger.error(f'{EMAIL_PASSWORD} environment variable is missing')
        rc = 55

    try:
        env_vars[ADMIN_EMAIL] = environ[ADMIN_EMAIL]
    except KeyError:
        logger.error(f'{ADMIN_EMAIL} environment variable is missing')
        rc = 55

    try:
        env_vars[MISCONDUCTS_EMAIL] = environ[MISCONDUCTS_EMAIL]
    except KeyError:
        logger.error(f'{MISCONDUCTS_EMAIL} environment variable is missing')
        rc = 55

    return rc, env_vars


def get_match_count(data, match):
    pattern = re.compile(match)

    return sum(1 for key in data.keys() if pattern.match(key))

def get_coaches_name(coaches, age_group, gender, team):
    try:
        return coaches[age_group][gender][team]
    except KeyError:
        return 'Unknown' 

def get_referees(payload):
    pattern = r'\.officials\.\d+\.position'
    found_cnt = get_match_count(payload, pattern)
    results = []
    for cnt in range(found_cnt):
        results.append({
            "name": payload[f'.officials.{cnt}.name'],
            "position": payload[f'.officials.{cnt}.position']
        })

# Make sure three referees are in the dictionary. Assumes missing positions are ARs
    for cnt in range(found_cnt, 3):
        results.append({
            "name": NOT_ASSIGNED,
            "position": "Asst. Referee"
        })
    return results

def get_misconducts(payload):
    pattern = r'\.misconductGrid\.\d+\.name'
    found_cnt = get_match_count(payload, pattern)
    results = []
    for cnt in range(found_cnt):
        results.append({
            "name": payload[f'.misconductGrid.{cnt}.name'],
            "role": payload[f'.misconductGrid.{cnt}.role'],
            "team": payload[f'.misconductGrid.{cnt}.team'],
            "minute": payload[f'.misconductGrid.{cnt}.minute'],
            "offense": payload[f'.misconductGrid.{cnt}.offense'],
            "description": payload[f'.misconductGrid.{cnt}.description'],
            "pass_number": payload[f'.misconductGrid.{cnt}.passIdNumber'],
            "caution_send_off": payload[f'.misconductGrid.{cnt}.cautionSendOff']
        })

    return results

def process_game_report(data):
    result = None
    if ADMIN_REVIEW not in data:
        if data[NARRATIVE]:
            data[ADMIN_REVIEW] = 'True'
        else:
            data[ADMIN_REVIEW] = None

    if ADMIN_NARRATIVE not in data:
        data[ADMIN_NARRATIVE] = None

    if CREW_CHANGES not in data:
        data[CREW_CHANGES] = None

    try:
        if NARRATIVE in data:
            narrative = data[NARRATIVE]
        else:
            narrative = None
        result = {
            "admin_review": set_boolean_value(data[ADMIN_REVIEW]),
            "misconduct": set_boolean_value(data['.misconductCheckbox']),
            "team_rosters": set_boolean_value(data['.teamRostersWereValid']),
            "lanyards": set_boolean_value(data['.didTheCoachEsWearTheirLanyards']),
            "borrowed_players": set_boolean_value(data['.teamsUsedBorrowedPlayers']),
            'assignments_correct': set_boolean_value(data['.assignmentsCorrect']),
            'home_team_score': data['.homeTeamScore'],
            'away_team_score': data['.awayTeamScore'],
            'officials': get_referees(data),
            'author': data['.author_name'],
            'game_dt': data[START_TIME],
            'home_team': data['.homeTeam'],
            'away_team': data['.awayTeam'],
            'venue_subvenue': data['.venue'],
            'league': data['.league'],
            'age_group': data['.ageGroup'],
            'gender': data['.gender'],
            'misconducts': get_misconducts(data),
            'home_coach': 'Unknown',
            'away_coach': 'Unknown',
            'narrative': narrative,
            'ejections': set_boolean_value(data['.ejections']),
            'admin_narrative': data[ADMIN_NARRATIVE],
            'crewChanges': data[CREW_CHANGES]
        }

    except KeyError as ke:
        logging.error(f"Key: {ke}, missing from process_game_report")

    return result