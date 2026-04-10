from datetime import datetime
import requests
import logging
from helpers.constants import START_TIME
from helpers.helpers import (format_date_yyyy_mm_dd, process_game_report,
                             get_coaches_name)

logger = logging.getLogger(__name__)

SEARCH_START_DT = "search[start_date]"
SEARCH_END_DT = "search[end_date]"


class Assignr:
    def __init__(self, client_id, client_secret, client_scope,
                 base_url, auth_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.client_scope = client_scope
        self.base_url = base_url
        self.auth_url = auth_url
        self.site_id = None
        self.token = None
        self.referees = {}
        self.assignors = {}

    def authenticate(self) -> None:
        form_data = {
            'client_secret': self.client_secret,
            'client_id': self.client_id,
            'scope': self.client_scope,
            'grant_type': 'client_credentials'
        }

        authenticate = requests.post(self.auth_url, data=form_data)

        try:
            self.token = authenticate.json()['access_token']
        except (KeyError, TypeError):
            logging.error('Token not found')
            self.token = None

    def get_site_id(self) -> None:
        rc, response = self.get_requests('/sites')
        try:
            if rc == 200:
                self.site_id = response['_embedded']['sites'][0]['id']
            else:
                logging.error(f"Response code {rc} returned for get_site_id")     
        except (KeyError, TypeError):
            logging.error('Site id not found')

    def get_requests(self, end_point, params=None):
        if not self.token:
            self.authenticate()

        headers = {
            'accept': 'application/json',
            'authorization': f'Bearer {self.token}'
        }

        # Logic manages pagination url
        if self.base_url in end_point:
            response = requests.get(end_point, headers=headers, params=params)
        else:
            response = requests.get(f"{self.base_url}{end_point}", headers=headers, params=params)
        return response.status_code, response.json()

    def load_referees_assignors(self):
        self.referees = {}
        self.assignors = {}
        page_nbr = 1
        more_rows = True

        if not self.token:
            self.authenticate()

        if self.site_id is None:
            self.get_site_id()

        while more_rows:
            params = {
                'page': page_nbr
            }
            status_code, response = self.get_requests(f'sites/{self.site_id}/users',
                                                      params=params)    
            if status_code != 200:
                logging.error(f'Failed to get users: {status_code}')
                more_rows = False
                return

            try:
                total_pages = response['page']['pages']
                for user in response['_embedded']['users']:
                    if user['official']:
                        self.referees[user['id']] = {
                            'first_name': user['first_name'],
                            'last_name': user['last_name'],
                            'email_addresses': user['email_addresses']
                        }
                    if user['assignor']:
                        self.assignors[user['id']] = {
                            'first_name': user['first_name'],
                            'last_name': user['last_name'],
                            'email_addresses': user['email_addresses']
                        }
            except KeyError as ke:
                logging.error(f"Key: {ke}, missing from Users response")

            page_nbr += 1
            if page_nbr > total_pages:
                more_rows = False

    def get_referees_by_assignments(self, payload):
        referees = []

        try:
            for official in payload:
                if '_embedded' in official and \
                    'official' in official['_embedded'] and \
                    'id' in official['_embedded']['official']:
                    referee_info = self.referees[official['_embedded']['official']['id']]
                    referees.append({
                        'accepted': official['accepted'],
                        'position': official['position'],
                        'first_name': referee_info['first_name'],
                        'last_name': referee_info['last_name'],
                        'email_addresses': referee_info['email_addresses']
                    })
        except KeyError as ke:
            logging.error(f"Key: {ke}, missing from Referee")
        return referees

    def get_game_information(self, payload):
        try:
            sub_item = payload["_embedded"]
            assignor = self.assignors[sub_item['assignor']['id']]
            referees = self.get_referees_by_assignments(sub_item['assignments'])
            sub_venue = payload["subvenue"] if "subvenue" in payload else None

            return {
                'id': payload["id"],
                'game_date': payload["localized_date"],
                'game_time': payload["localized_time"],
                'start_time': payload["start_time"],
                'home_team': payload["home_team"],
                'away_team': payload["away_team"],
                'age_group': payload["age_group"],
                'league': payload["league"],
                'venue': sub_item["venue"],
                'sub_venue': sub_venue,
                'gender': payload["gender"],
                'game_type': payload["game_type"],
                'cancelled': payload["cancelled"],
                'referees': referees,
                'assignor': assignor 
            }
        except KeyError as ke:
            logging.error(f"Key: {ke}, missing from Game Information Function")
            return {
                'id': payload["id"],
                'game_date': None,
                'game_time': None,
                'start_time': None,
                'home_team': None,
                'away_team': None,
                'age_group': None,
                'league': None,
                'venue': None,
                'sub_venue': None,
                'gender': None,
                'game_type': None,
                'cancelled': None,
                'referees': None,
                'assignor': None                 
            }

    def get_reports(self, start_dt, end_dt, assignors, coaches):
        if not self.token:
            self.authenticate()

        misconducts = []
        admin_reports = []
        assignor_reports = []
        team_rosters = []
        lanyards = []
        borrowed_players = []
        page_nbr = 1
        more_rows = True

        reports = {
            "misconducts": misconducts,
            "admin_reports": admin_reports,
            'assignor_reports': assignor_reports,
            'team_rosters': team_rosters,
            'lanyards': lanyards,
            'borrowed_players': borrowed_players
        }

        if self.site_id is None:
            self.get_site_id()

# Change from 108 to 1002 when CYSL game report implemented.
        while more_rows:
            params = {
                'page': page_nbr,
                SEARCH_START_DT: start_dt,
                SEARCH_END_DT: end_dt
            }
            status_code, response = self.get_requests('form/templates/1002/submissions',
                                                      params=params)    
            if status_code != 200:
                logging.error(f'Failed to get reports: {status_code}')
                more_rows = False
                return reports

            try:
                total_pages = response['page']['pages']
                for item in response['_embedded']['form_submissions']:
                    data_dict = {}
                    for data in item['_embedded']['values']:
                        data_dict[data['key']] = data['value']

                    data_dict[START_TIME] = datetime.fromisoformat(data_dict[START_TIME])
                    data_dict['.author_name'] = item['author_name']
                    result = process_game_report(data_dict)
                    result['home_coach'] = get_coaches_name(coaches, result['age_group'], \
                                                            result['gender'], result['home_team'])
                    result['away_coach'] = get_coaches_name(coaches, result['age_group'], \
                                                            result['gender'], result['away_team'])
                    if result['admin_review']:
                        reports['admin_reports'].append(result)
                    if not result['team_rosters']:
                        reports['team_rosters'].append(result)
                    if not result['lanyards']:
                        reports['lanyards'].append(result)
                    if result['borrowed_players']:
                        reports['borrowed_players'].append(result)
                    if result['misconduct']:
                        result['assignors'] = assignors[result['league']]
                        reports['misconducts'].append(result)
                    if result['assignments_correct'] == False:
                        result['assignors'] = assignors[result['league']]
                        reports['assignor_reports'].append(result)

            except KeyError as ke:
                logging.error(f"Key: {ke}, missing from Game Report response")

            page_nbr += 1
            if page_nbr > total_pages:
                more_rows = False

        return reports

    def get_availability(self, user_id, start_dt, end_dt):
        availability = []
        params = {
           'user_id': user_id,
           SEARCH_START_DT: start_dt,
           SEARCH_END_DT: end_dt
       }

        status_code, response = self.get_requests(
            f'users/{user_id}/availability', params=params)

        if status_code == 404:
            logger.warning(f'User: {user_id} has no availability')
            return availability

        if status_code != 200:
            logger.error(f'Failed return code: {status_code} for user: {user_id}')
            return availability

        try:
            for avail in response['_embedded']['availability']:
                if avail['all_day'] == 'true':
                    availability.append({
                        'date': avail['date'],
                        'avail': 'ALL DAY'                 
                    })
                else:
                    availability.append({
                        'date': avail['date'],
                        'avail': f"{avail['start_time']} - {avail['end_time']}"                 
                    })

        except KeyError as ke:
            logger.error(f"Key: {ke}, missing from Availability response")

        return availability

    def match_games_to_reports(self, start_dt, end_dt, games):
        if not self.token:
            self.authenticate()

        page_nbr = 1
        more_rows = True

        if self.site_id is None:
            self.get_site_id()

        while more_rows:
            params = {
                'page': page_nbr,
                SEARCH_START_DT: start_dt,
                SEARCH_END_DT: end_dt
            }
            status_code, response = self.get_requests('form/templates/1002/submissions',
                                                      params=params)    
            if status_code != 200:
                logging.error(f'Failed to get game reports: {status_code}')
                more_rows = False
                return games

            try:
                total_pages = response['page']['pages']
                for item in response['_embedded']['form_submissions']:
                    game_id = item["_embedded"]['game']['id']
                    game_report_url = item['_links']['game_report_webview']['href']
                    if game_id in games:
                        data_dict = {}
                        for data in item['_embedded']['values']:
                            data_dict[data['key']] = data['value']
                        away_roster = True if ".uploadAwayTeamRoster.0.url" in data_dict and \
                                data_dict[".uploadAwayTeamRoster.0.url"] != [] else False
                        home_roster = True if ".uploadHomeTeamRoster.0.url" in data_dict and \
                                data_dict[".uploadHomeTeamRoster.0.url"] != [] else False
                        games[game_id]['game_report_url'] = game_report_url
                        games[game_id]['home_roster'] = home_roster
                        games[game_id]['away_roster'] = away_roster

            except KeyError as ke:
                logging.error(f"Key: {ke}, missing from Game Report response")

            page_nbr += 1
            if page_nbr > total_pages:
                more_rows = False

        return games
    
    def get_game_ids(self, start_dt, end_dt, game_type="Coastal"):
        results = {}
        if not self.token:
            self.authenticate()

        page_nbr = 1
        more_rows = True

        if self.site_id is None:
            self.get_site_id()

        params = {
            SEARCH_START_DT: format_date_yyyy_mm_dd(start_dt),
            SEARCH_END_DT: format_date_yyyy_mm_dd(end_dt),
            'page': page_nbr,
            'limit': 50
        }

        while more_rows:
            status_code, response = self.get_requests(f'sites/{self.site_id}/games',
                                                      params=params)
            if status_code != 200:
                logging.error(f'Failed to get reports: {status_code}')
                more_rows = False
                return results

            try:
                total_pages = response['page']['pages']
                for item in response['_embedded']['games']:
                    if item['game_type'] == game_type:
                        game_info = self.get_game_information(item)
                        game_info['game_report_url'] = None
                        game_info['home_roster'] = None
                        game_info['away_roster'] = None
                        results[item['id']] = game_info

            except KeyError as ke:
                logging.error(f"Key: {ke}, missing from Game Report response")

            page_nbr += 1
            params['page'] = page_nbr
            if page_nbr > total_pages:
                more_rows = False

        return results

    def get_league_games(self, league, start_dt, end_dt):
        results = []

        params = {
            SEARCH_START_DT: format_date_yyyy_mm_dd(start_dt),
            SEARCH_END_DT: format_date_yyyy_mm_dd(end_dt)
        }

        if self.site_id is None:
            self.get_site_id()

        status_code, response = self.get_requests(f'sites/{self.site_id}/games',
                                                  params=params)

        if status_code != 200:
            logging.error(f'Failed to get games: {status_code}')
            return results

        try:
            for item in response['_embedded']['games']:
                if item['league'] == league:
                    game_info = self.get_game_information(item)
                    results.append(game_info)

        except KeyError as ke:
            logging.error(f"Key: {ke}, missing from Game response")

        return results

    def get_assignors(self):
        results = []
        if not self.token:
            self.authenticate()

        page_nbr = 1
        more_rows = True

        if self.site_id is None:
            self.get_site_id()

        while more_rows:
            status_code, response = self.get_requests(f'sites/{self.site_id}/users',
                                                      params={'page': page_nbr})
            if status_code != 200:
                logging.error(f'Failed to get reports: {status_code}')
                more_rows = False
                return results

            try:
                total_pages = response['page']['pages']
                for item in response['_embedded']['users']:
                    if item['assignor'] and item['active']:
                        results.append({
                            'first_name': item['first_name'],
                            'last_name': item['last_name'],
                            'email': item['email_addresses'][0]
                        })

            except KeyError as ke:
                logging.error(f"Key: {ke}, missing from Game Report response")

            page_nbr += 1
            if page_nbr > total_pages:
                more_rows = False

        return results
