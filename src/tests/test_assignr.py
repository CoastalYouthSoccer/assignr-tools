import sys
from os.path import join, abspath, dirname
from datetime import datetime
import json
from unittest import TestCase
from unittest.mock import (patch, MagicMock)
from assignr.assignr import Assignr

ACCESS_TOKEN = "ACCESS_TOKEN"
BASE_URL = "https://base.com"
AUTH_URL = "https://auth.com"
ASSIGNR_REQUESTS ="assignr.assignr.requests"
CONST_DATE_2022_01_01 = datetime(2022,1,1,0,0,0,0)

response_file_dir = join(dirname(abspath(__file__)), 'mock_responses')

mock_auth_response = MagicMock()
mock_auth_response.status_code = 200
mock_auth_response.json.return_value = {
    "access_token": ACCESS_TOKEN,
    "token_type": "Bearer",
    "scope": "read",
    "created_at": 1606420331
}


class TestAssignr(TestCase):
    def test_valid_init(self):
        temp = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        self.assertEqual(temp.client_id, '123')
        self.assertEqual(temp.client_secret, '234')
        self.assertEqual(temp.client_scope, '345')
        self.assertEqual(temp.base_url, BASE_URL)
        self.assertEqual(temp.auth_url, AUTH_URL)
        self.assertIsNone(temp.site_id)
        self.assertIsNone(temp.token)

    @patch(ASSIGNR_REQUESTS)
    def test_valid_authentication(self, mock_requests):
        mock_requests.post.return_value = mock_auth_response

        temp = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        temp.authenticate()
        self.assertEqual(temp.token, ACCESS_TOKEN)

    @patch(ASSIGNR_REQUESTS)
    def test_invalid_authentication(self, mock_requests):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token_type": "Bearer",
            "scope": "read",
            "created_at": 1606420331
        }
        mock_requests.post.return_value = mock_response

        temp = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        with self.assertLogs(level='INFO') as cm:
            temp.authenticate()
        self.assertEqual(cm.output, ["ERROR:root:Token not found"])
        self.assertIsNone(temp.token)

    @patch(ASSIGNR_REQUESTS)
    def test_valid_site_id(self, mock_requests):
        mock_requests.post.return_value = mock_auth_response

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "page": {
                "records": 1,
                "pages": 1,
                "current_page": 1,
                "limit": 50
            },
            "_embedded": {
                "sites": [
                    {
                        "id": 123456,
                        "name": "Test League",
                        "show_game_requests": "false",
                        "show_unassigned_games": "true",
                        "show_all_games": "false",
                        "show_game_reports": "true",
                        "forms_enabled": "false",
                        "sports": [
                            "soccer"
                        ]
                    }
                ]
            },
            "_links": {
                "self": {
                    "href": "https://api.assignr.com/v2/sites?page=1"
                }
            }
        }

        mock_requests.get.return_value = mock_response

        temp = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        temp.get_site_id()
        self.assertEqual(temp.site_id, 123456)

    @patch(ASSIGNR_REQUESTS)
    def test_invalid_site_id(self, mock_requests):
        mock_requests.post.return_value = mock_auth_response

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "page": {
                "records": 1,
                "pages": 1,
                "current_page": 1,
                "limit": 50
            },
            "_links": {
                "self": {
                    "href": "https://api.assignr.com/v2/sites?page=1"
                }
            }
        }

        mock_requests.get.return_value = mock_response

        temp = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        with self.assertLogs(level='INFO') as cm:
            temp.get_site_id()
        self.assertEqual(cm.output, ["ERROR:root:Site id not found"])
        self.assertIsNone(temp.site_id)


    @patch(ASSIGNR_REQUESTS)
    def test_site_id_invalid_response(self, mock_requests):
        mock_requests.post.return_value = mock_auth_response

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_requests.get.return_value = mock_response

        temp = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        with self.assertLogs(level='INFO') as cm:
            temp.get_site_id()
        self.assertIsNone(temp.site_id)
        self.assertEqual(cm.output, ["ERROR:root:Response code 500 returned for get_site_id"])

    def test_get_referees_by_availability(self):
        temp = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        temp.referees = {
            12656: {
                'first_name': 'Mickey',
                'last_name': 'Mouse',
                'email_addresses': ['mickey@disney.mouse']
            },
            12761: {
                'first_name': 'Homer',
                'last_name': 'Simpson',
                'email_addresses': ['homer@springfield.simpson']                
            }
        }
        expected_result = [
            {
                'accepted': 'false',
                'position': 'Referee',
                'first_name': 'Mickey',
                'last_name': 'Mouse',
                'email_addresses': ['mickey@disney.mouse']
            }, {
                'accepted': 'true',
                'position': 'Scorekeeper',
                'first_name': 'Homer',
                'last_name': 'Simpson',
                'email_addresses': ['homer@springfield.simpson']
            }
        ]
        payload = [
        {
            "id": 63558183,
            "position_id": 78498,
            "position": "Referee",
            "position_abbreviation": "R",
            "accepted": "false",
            "declined": "false",
            "assigned": "false",
            "sort_order": 1,
            "lock_version": 2,
            "created": "2024-01-03T22:51:20.000-05:00",
            "updated": "2024-01-04T12:45:56.000-05:00"
        },
        {
            "id": 63558186,
            "position_id": 78498,
            "position": "Referee",
            "position_abbreviation": "R",
            "accepted": "false",
            "declined": "false",
            "assigned": "true",
            "sort_order": 2,
            "lock_version": 1,
            "created": "2024-01-03T22:51:20.000-05:00",
            "updated": "2024-01-04T12:44:16.000-05:00",
            "_embedded": {
                "official": {
                    "id": 12656,
                    "last_name": "Mouse",
                    "first_name": "Mickey",
                    "created": "2023-11-07T20:49:27.000-05:00",
                    "updated": "2024-02-18T11:58:02.000-05:00"
                }
            }
        },
        {
            "id": 63558189,
            "position_id": 83433,
            "position": "Scorekeeper",
            "position_abbreviation": "S",
            "accepted": "true",
            "declined": "false",
            "assigned": "true",
            "sort_order": 3,
            "lock_version": 1,
            "created": "2024-01-03T22:51:20.000-05:00",
            "updated": "2024-01-04T12:40:58.000-05:00",
            "_embedded": {
                "official": {
                    "id": 12761,
                    "last_name": "Simpson",
                    "first_name": "Homer",
                    "created": "2023-10-05T18:41:33.000-04:00",
                    "updated": "2024-02-15T20:16:55.000-05:00"
                }
            }
        }]
 
        referees = temp.get_referees_by_assignments(payload)
        self.assertEqual(referees, expected_result)

    @patch(ASSIGNR_REQUESTS)
    def test_invalid_get_reports(self, mock_requests):
        mock_requests.post.return_value = mock_auth_response

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {}

        mock_requests.get.return_value = mock_response

        temp = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        temp.site_id = 100
        with self.assertLogs(level='INFO') as cm:
            result = temp.get_reports(CONST_DATE_2022_01_01,
                                        CONST_DATE_2022_01_01,
                                        None,
                                        None)
        self.assertEqual(cm.output, ["ERROR:root:Failed to get reports: 500"])
        self.assertEqual(result, {'misconducts': [], 'admin_reports': [],
                                  'assignor_reports': []})

    @patch(ASSIGNR_REQUESTS)
    def test_valid_get_availability(self, mock_requests):
        mock_requests.post.return_value = mock_auth_response

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "page": {
                "records": 3,
                "pages": 1,
                "current_page": 1,
                "limit": 200
            },
            "_embedded": {
                "availability": [
                    {
                        "id": 7518668545,
                        "date": "2024-02-10",
                        "all_day": "true",
                        "description": "all day",
                        "created": "2024-02-04T19:52:21.000-05:00"
                    },
                    {
                        "id": 7518669171,
                        "date": "2024-02-17",
                        "all_day": "false",
                        "description": "8a-11a",
                        "start_time": "8:00 AM",
                        "end_time": "11:00 AM",
                        "created": "2024-02-04T19:53:53.000-05:00",
                        "updated": "2024-02-04T19:54:23.000-05:00"
                    },
                    {
                        "id": 75186694755,
                        "date": "2024-02-17",
                        "all_day": "false",
                        "description": "4p-8p",
                        "start_time": "4:00 PM",
                        "end_time": "8:00 PM",
                        "created": "2024-02-04T19:54:23.000-05:00",
                        "updated": "2024-02-04T19:54:23.000-05:00"
                    }
                ]
            },
            "_links": {
                "self": {
                    "href": "https://api.assignr.com/v2/users/12345/availability?page=1&search%5Bend_date%5D=02%2F29%2F2024&search%5Bstart_date%5D=01%2F01%2F2024"
                }
            }
        }

        mock_requests.get.return_value = mock_response

        temp = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        temp.site_id = 100
        result = temp.get_availability(12345, '01/01/2024', '02/28/2024')
        self.assertEqual(result, [
            {'date': '2024-02-10', 'avail': 'ALL DAY'},
            {'date': '2024-02-17', 'avail': '8:00 AM - 11:00 AM'},
            {'date': '2024-02-17', 'avail': '4:00 PM - 8:00 PM'}
        ])

    @patch(ASSIGNR_REQUESTS)
    def test_valid_get_availability_404_code(self, mock_requests):
        mock_requests.post.return_value = mock_auth_response

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {}

        mock_requests.get.return_value = mock_response

        temp = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        temp.site_id = 100
        with self.assertLogs(level='INFO') as cm:
            result = temp.get_availability(123, '01/01/2022', '01/01/2022')
        self.assertEqual(cm.output, ["WARNING:assignr.assignr:User: 123 has no availability"])
        self.assertEqual(result, [])

    @patch(ASSIGNR_REQUESTS)
    def test_valid_get_availability_500_code(self, mock_requests):
        mock_requests.post.return_value = mock_auth_response

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {}

        mock_requests.get.return_value = mock_response

        temp = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        temp.site_id = 100
        with self.assertLogs(level='INFO') as cm:
            result = temp.get_availability(123, '01/01/2022', '01/01/2022')
        self.assertEqual(cm.output, ["ERROR:assignr.assignr:Failed return code: 500 for user: 123"])
        self.assertEqual(result, [])

    @patch(ASSIGNR_REQUESTS)
    def test_valid_get_availability_key_error(self, mock_requests):
        mock_requests.post.return_value = mock_auth_response

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "page": {
                "records": 3,
                "pages": 1,
                "current_page": 1,
                "limit": 200
            },
            "_embedded": {
                "availability": [
                    {
                        "id": 7518668545,
                        "date": "2024-02-10",
                        "description": "all day",
                        "created": "2024-02-04T19:52:21.000-05:00"
                    },
                    {
                        "id": 7518669171,
                        "date": "2024-02-17",
                        "description": "8a-11a",
                        "start_time": "8:00 AM",
                        "end_time": "11:00 AM",
                        "created": "2024-02-04T19:53:53.000-05:00",
                        "updated": "2024-02-04T19:54:23.000-05:00"
                    },
                    {
                        "id": 75186694755,
                        "date": "2024-02-17",
                        "description": "4p-8p",
                        "start_time": "4:00 PM",
                        "end_time": "8:00 PM",
                        "created": "2024-02-04T19:54:23.000-05:00",
                        "updated": "2024-02-04T19:54:23.000-05:00"
                    }
                ]
            },
            "_links": {
                "self": {
                    "href": "https://api.assignr.com/v2/users/12345/availability?page=1&search%5Bend_date%5D=02%2F29%2F2024&search%5Bstart_date%5D=01%2F01%2F2024"
                }
            }
        }
        mock_requests.get.return_value = mock_response

        temp = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        temp.site_id = 100
        with self.assertLogs(level='INFO') as cm:
            result = temp.get_availability(123, '01/01/2022', '01/01/2022')
        self.assertEqual(cm.output, 
            ["ERROR:assignr.assignr:Key: 'all_day', missing from Availability response"])
        self.assertEqual(result, [])


class TestGetGameIds(TestCase):

    def setUp(self):
        self.instance = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        self.instance.token = None
        self.instance.site_id = None

    @patch.object(Assignr, 'get_game_information')
    @patch.object(Assignr, 'get_requests')
    @patch.object(Assignr, 'get_site_id')
    @patch.object(Assignr, 'authenticate')
    @patch('helpers.helpers.format_date_yyyy_mm_dd')
    def test_get_game_ids(self, mock_format_date, mock_authenticate,
                          mock_get_site_id, mock_get_requests, mock_get_game_information):
        mock_format_date.side_effect = lambda dt: dt.strftime('%Y-%m-%d')

        self.instance.token = None
        mock_authenticate.side_effect = lambda: setattr(self.instance, 'token', 'dummy_token')

        mock_get_site_id.side_effect = lambda: setattr(self.instance, 'site_id', 123)

        mock_get_requests.side_effect = [
            (200, {
                'page': {'pages': 2},
                '_embedded': {'games': [{'id': 1, 'game_type': 'Coastal'}, {'id': 2, 'game_type': 'Other'}]}
            }),
            (200, {
                'page': {'pages': 2},
                '_embedded': {'games': [{'id': 3, 'game_type': 'Coastal'}, {'id': 4, 'game_type': 'Other'}]}
            })
        ]

        # Mocking get_game_information to return game details
        mock_get_game_information.side_effect = lambda game: {'game_id': game['id'], 'info': 'some_info'}

        # Call the method under test
        start_dt = "2024-09-01"
        end_dt = "2024-09-15"
        result = self.instance.get_game_ids(start_dt, end_dt, game_type="Coastal")

        # Expected result with only Coastal games
        expected_result = {
            1: {'game_id': 1, 'info': 'some_info', 'game_report_url': None, 'home_roster': None, 'away_roster': None},
            3: {'game_id': 3, 'info': 'some_info', 'game_report_url': None, 'home_roster': None, 'away_roster': None}
        }

        # Assertions
        self.assertEqual(result, expected_result)

        # Verify that the authenticate method was called
        mock_authenticate.assert_called_once()

        # Verify that the get_site_id method was called
        mock_get_site_id.assert_called_once()

        # Verify that the API was called twice (pagination)
        self.assertEqual(mock_get_requests.call_count, 2)

        # Verify that the game information was retrieved for the correct game types
        mock_get_game_information.assert_any_call({'id': 1, 'game_type': 'Coastal'})
        mock_get_game_information.assert_any_call({'id': 3, 'game_type': 'Coastal'})


class TestGameInformation(TestCase):
    def setUp(self):
        self.instance = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        self.instance.referees = {
            12656: {
                'first_name': 'Mickey',
                'last_name': 'Mouse',
                'email_addresses': ['mickey@disney.mouse']
            },
            12761: {
                'first_name': 'Homer',
                'last_name': 'Simpson',
                'email_addresses': ['homer@springfield.simpson']                
            }
        }
        self.instance.assignors = {
            123: {
                'first_name': 'Marge',
                'last_name': 'Simpson',
                'email_addresses': ['marge@springfield.simpson']                
            }
        }
    def test_get_game_information(self):
        payload = {
            "id": 101,
            "localized_date": "2024-09-01",
            "localized_time": "15:00",
            "start_time": "14:45",
            "home_team": "Team A",
            "away_team": "Team B",
            "age_group": "U12",
            "league": "Youth League",
            "gender": "M",
            "game_type": "Friendly",
            "cancelled": False,
            "_embedded": {
                "assignor": {"id": 123},
                "assignments": [
                    {
                        'position': 'Referee',
                        'accepted': True,
                        '_embedded': {'official': {'id': 12656}}
                    }, {
                        'position': 'Assistant Referee',
                        'accepted': True,
                        '_embedded': {'official': {'id': 12761}}
                    }
                ],
                "venue": "Stadium A"
            },
            "subvenue": "Field 2"
        }

        # Call the method under test
        result = self.instance.get_game_information(payload)

        # Assert that the result matches the expected output
        expected_result = {
            'id': 101,
            'game_date': '2024-09-01',
            'game_time': '15:00',
            'start_time': '14:45',
            'home_team': 'Team A',
            'away_team': 'Team B',
            'age_group': 'U12',
            'league': 'Youth League',
            'venue': "Stadium A",
            'sub_venue': "Field 2",
            'gender': 'M',
            'game_type': 'Friendly',
            'cancelled': False,
            'referees': [
                {'accepted': True, 'position': 'Referee',
                 'first_name': 'Mickey', 'last_name': 'Mouse',
                 'email_addresses': ['mickey@disney.mouse']},
                {'accepted': True, 'position': 'Assistant Referee',
                 'first_name': 'Homer', 'last_name': 'Simpson',
                 'email_addresses': ['homer@springfield.simpson']}
            ],
            'assignor': {'first_name': 'Marge', 'last_name': 'Simpson',
                         'email_addresses': ['marge@springfield.simpson']}
        }

        self.assertEqual(result, expected_result)

    def test_get_game_information_keyerror(self):
        temp = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        temp.site_id = 100
        temp.referees = {
            12656: {
                'first_name': 'Mickey',
                'last_name': 'Mouse',
            },
            12761: {
                'first_name': 'Homer',
                'email_addresses': ['homer@springfield.simpson']                
            }            
        }
        payload = {
            "id": 101,
            "localized_date": "2024-09-01",
            "localized_time": "15:00",
            "start_time": "14:45",
            "home_team": "Team A",
            "away_team": "Team B",
            "age_group": "U12",
            "league": "Youth League",
            "gender": "M",
            "game_type": "Friendly",
            "cancelled": False,
            "_embedded": {
                "assignor": {"id": 123},
                "assignments": [
                    {
                        'position': 'Referee',
                        'accepted': True,
                        '_embedded': {'official': {'id': 12656}}
                    }, {
                        'position': 'Assistant Referee',
                        'accepted': True,
                        '_embedded': {'official': {'id': 12761}}
                    }
                ],
                "venue": "Stadium A"
            },
            "subvenue": "Field 2"
        }
        expected_result = {
            'id': 101, 'game_date': None, 'game_time': None, 'start_time': None,
            'home_team': None, 'away_team': None, 'age_group': None, 'league': None,
            'venue': None, 'sub_venue': None, 'gender': None, 'game_type': None,
            'cancelled': None, 'referees': None, 'assignor': None
        }

        with self.assertLogs(level='INFO') as cm:
            result = temp.get_game_information(payload)

        self.assertEqual(cm.output, ["ERROR:root:Key: 123, missing from Game Information Function"])
        self.assertEqual(result, expected_result)

        # Assert that the result contains None values for missing fields
        expected_result = {
            'id': 101,
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

        self.assertEqual(result, expected_result)


class TestMatchGamesToReports(TestCase):

    def setUp(self):
        # Set up the instance of the class that contains match_games_to_reports
        self.instance = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        self.instance.token = 'dummy_token'
        self.instance.site_id = 123

    @patch.object(Assignr, 'get_requests')
    @patch.object(Assignr, 'get_site_id')
    @patch.object(Assignr, 'authenticate')
    def test_match_games_to_reports(self, mock_authenticate, mock_get_site_id, mock_get_requests):
        # Mock authenticate to simulate token generation if needed
        mock_authenticate.side_effect = lambda: setattr(self.instance, 'token', 'new_dummy_token')

        # Mock get_site_id to set a dummy site_id if needed
        mock_get_site_id.side_effect = lambda: setattr(self.instance, 'site_id', 456)

        # Simulating API responses with pagination (2 pages)
        mock_get_requests.side_effect = [
            (200, {
                'page': {'pages': 2},
                '_embedded': {'form_submissions': [
                    {
                        "_embedded": {
                            "game": {"id": 1},
                            "values": [
                                {"key": ".uploadHomeTeamRoster.0.url", "value": ["home_roster_url"]},
                                {"key": ".uploadAwayTeamRoster.0.url", "value": ["away_roster_url"]}
                            ]
                        },
                        "_links": {'game_report_webview': {'href': 'game_report_url_1'}}
                    }
                ]}
            }),
            (200, {
                'page': {'pages': 2},
                '_embedded': {'form_submissions': [
                    {
                        "_embedded": {
                            "game": {"id": 2},
                            "values": [
                                {"key": ".uploadHomeTeamRoster.0.url", "value": []},  # no home roster
                                {"key": ".uploadAwayTeamRoster.0.url", "value": ["away_roster_url"]}
                            ]
                        },
                        "_links": {'game_report_webview': {'href': 'game_report_url_2'}}
                    }
                ]}
            })
        ]

        # Simulating the input 'games' dictionary
        games = {
            1: {'game_report_url': None, 'home_roster': None, 'away_roster': None},
            2: {'game_report_url': None, 'home_roster': None, 'away_roster': None}
        }

        # Define start and end dates
        start_dt = "2024-09-01"
        end_dt = "2024-09-15"

        # Call the method under test
        result = self.instance.match_games_to_reports(start_dt, end_dt, games)

        # Expected result after processing both pages
        expected_result = {
            1: {'game_report_url': 'game_report_url_1', 'home_roster': True, 'away_roster': True},
            2: {'game_report_url': 'game_report_url_2', 'home_roster': False, 'away_roster': True}
        }

        # Assert that the games dictionary is updated as expected
        self.assertEqual(result, expected_result)

        # Check that no errors occurred
        mock_authenticate.assert_not_called()  # token was already set

    @patch.object(Assignr, 'get_requests')
    def test_match_games_to_reports_keyerror_handling(self, mock_get_requests):
        # Simulate a response missing required keys to trigger KeyError
        mock_get_requests.return_value = (200, {
            'page': {'pages': 1},
            '_embedded': {'form_submissions': [
                {
                    "_embedded": {
                        "game": {"id": 1},
                        "values": []
                    },
                    "_links": {'game_report_webview': {'href': 'game_report_url_1'}}
                }
            ]}
        })

        # Simulating the input 'games' dictionary
        games = {
            1: {'game_report_url': None, 'home_roster': None, 'away_roster': None}
        }

        # Define start and end dates
        start_dt = "2024-09-01"
        end_dt = "2024-09-15"

        # Call the method under test
        result = self.instance.match_games_to_reports(start_dt, end_dt, games)

        # Expected result should still update the game_report_url but no roster info due to missing keys
        expected_result = {
            1: {'game_report_url': 'game_report_url_1', 'home_roster': False, 'away_roster': False}
        }

        # Assert that the games dictionary is updated correctly
        self.assertEqual(result, expected_result)


class TestGetGameIds(TestCase):

    def setUp(self):
        # Set up an instance of the class that contains get_game_ids
        self.instance = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        self.instance.token = None  # simulate no token
        self.instance.site_id = None  # simulate no site_id

    @patch.object(Assignr, 'get_requests')
    @patch.object(Assignr, 'get_game_information')
    @patch.object(Assignr, 'get_site_id')
    @patch.object(Assignr, 'authenticate')
    @patch('helpers.helpers.format_date_yyyy_mm_dd')
    def test_get_game_ids(self, mock_format_date, mock_authenticate, mock_get_site_id, mock_get_game_information, mock_get_requests):
        # Mocking format_date_yyyy_mm_dd
        mock_format_date.side_effect = lambda dt: dt

        # Mocking the authenticate and get_site_id methods
        mock_authenticate.side_effect = lambda: setattr(self.instance, 'token', 'dummy_token')
        mock_get_site_id.side_effect = lambda: setattr(self.instance, 'site_id', 123)

        # Simulating API response with pagination (2 pages)
        mock_get_requests.side_effect = [
            (200, {
                'page': {'pages': 2},
                '_embedded': {'games': [
                    {'id': 1, 'game_type': 'Coastal'},
                    {'id': 2, 'game_type': 'Other'}
                ]}
            }),
            (200, {
                'page': {'pages': 2},
                '_embedded': {'games': [
                    {'id': 3, 'game_type': 'Coastal'}
                ]}
            })
        ]

        # Mocking get_game_information to return dummy game info
        mock_get_game_information.side_effect = lambda item: {
            'id': item['id'],
            'game_report_url': None,
            'home_roster': None,
            'away_roster': None
        }

        # Define the date range and game type
        start_dt = "2024-09-01"
        end_dt = "2024-09-15"
        game_type = "Coastal"

        # Call the method under test
        result = self.instance.get_game_ids(start_dt, end_dt, game_type)

        # Expected result only includes Coastal games
        expected_result = {
            1: {'id': 1, 'game_report_url': None, 'home_roster': None, 'away_roster': None},
            3: {'id': 3, 'game_report_url': None, 'home_roster': None, 'away_roster': None}
        }

        # Assert that the result matches the expected result
        self.assertEqual(result, expected_result)

        # Verify that the methods were called correctly
        mock_authenticate.assert_called_once()  # authenticate should be called since token is None
        mock_get_site_id.assert_called_once()  # get_site_id should be called since site_id is None

        # Check that get_requests was called twice (pagination handling)
        self.assertEqual(mock_get_requests.call_count, 2)


class TestGetAssignors(TestCase):

    def setUp(self):
        # Set up an instance of the class that contains get_assignors
        self.instance = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        self.instance.token = None  # simulate no token
        self.instance.site_id = None  # simulate no site_id

    @patch.object(Assignr, 'get_requests')
    @patch.object(Assignr, 'get_site_id')
    @patch.object(Assignr, 'authenticate')
    def test_get_assignors_success(self, mock_authenticate, mock_get_site_id, mock_get_requests):
        # Mock the authenticate and get_site_id methods
        mock_authenticate.side_effect = lambda: setattr(self.instance, 'token', 'dummy_token')
        mock_get_site_id.side_effect = lambda: setattr(self.instance, 'site_id', 123)

        # Mocking the response for the first page of users
        mock_get_requests.side_effect = [
            (200, {
                'page': {'pages': 2},
                '_embedded': {'users': [
                    {'first_name': 'John', 'last_name': 'Doe', 'email_addresses': ['john@example.com'], 'assignor': True, 'active': True},
                    {'first_name': 'Jane', 'last_name': 'Smith', 'email_addresses': ['jane@example.com'], 'assignor': False, 'active': True},
                ]}
            }),
            (200, {
                'page': {'pages': 2},
                '_embedded': {'users': [
                    {'first_name': 'Emily', 'last_name': 'Davis', 'email_addresses': ['emily@example.com'], 'assignor': True, 'active': True},
                    {'first_name': 'Chris', 'last_name': 'Brown', 'email_addresses': ['chris@example.com'], 'assignor': True, 'active': False},
                ]}
            })
        ]

        # Call the method under test
        result = self.instance.get_assignors()

        # Expected result should only include active assignors
        expected_result = [
            {'first_name': 'John', 'last_name': 'Doe', 'email': 'john@example.com'},
            {'first_name': 'Emily', 'last_name': 'Davis', 'email': 'emily@example.com'}
        ]

        # Assert that the result matches the expected result
        self.assertEqual(result, expected_result)

        # Verify that the methods were called correctly
        mock_authenticate.assert_called_once()  # authenticate should be called since token is None
        mock_get_site_id.assert_called_once()  # get_site_id should be called since site_id is None

        # Check that get_requests was called twice (pagination handling)
        self.assertEqual(mock_get_requests.call_count, 2)
        mock_get_requests.assert_any_call(
            'sites/123/users',
            params={'page': 1}
        )
        mock_get_requests.assert_any_call(
            'sites/123/users',
            params={'page': 2}
        )


class TestGetLeagueGames(TestCase):
    def setUp(self):
        # Set up an instance of the class that contains get_assignors
        self.instance = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        self.instance.token = None  # simulate no token
        self.instance.site_id = None  # simulate no site_id

    @patch.object(Assignr, 'get_requests')
    @patch.object(Assignr, 'get_site_id')
    def test_successful_response(self, mock_get_site_id, mock_get_requests):
        mock_get_site_id.side_effect = lambda: setattr(self.instance, 'site_id', 123)

        mock_get_requests.return_value = (200, {
            '_embedded': {
                'games': [
                    {'id': 1, 'league': 'Premier', 'game_type': 'Type1'},
                    {'id': 2, 'league': 'Championship', 'game_type': 'Type2'}
                ]
            }
        })

        # Test
        league = 'Premier'
        start_dt = '2024-01-01'
        end_dt = '2024-01-31'
        result = self.instance.get_league_games(league, start_dt, end_dt)

        # Assertions
        self.assertEqual(len(result), 1)  # Only 1 game from the Premier league
        self.assertEqual(result[0]['id'], 1)

    @patch.object(Assignr, 'get_requests')
    @patch.object(Assignr, 'get_site_id')
    def test_failed_api_call(self, mock_get_site_id, mock_get_requests):
        mock_get_site_id.side_effect = lambda: setattr(self.instance, 'site_id', 123)
        mock_get_requests.return_value = (500, None)

        # Test
        league = 'Premier'
        start_dt = '2024-01-01'
        end_dt = '2024-01-31'
        result = self.instance.get_league_games(league, start_dt, end_dt)

        # Assertions
        self.assertEqual(result, [])  # No results on failed API call
#        mock_logger.error.assert_called_once_with('Failed to get games: 500')

    @patch.object(Assignr, 'get_requests')
    @patch.object(Assignr, 'get_site_id')
    def test_key_error_in_response(self, mock_get_site_id, mock_get_requests):
        mock_get_site_id.side_effect = lambda: setattr(self.instance, 'site_id', 123)

        # Simulate missing keys in the response
        mock_get_requests.return_value = (200, {
            '_embedded': {}  # Missing 'games'
        })

        # Test
        league = 'Premier'
        start_dt = '2024-01-01'
        end_dt = '2024-01-31'
        result = self.instance.get_league_games(league, start_dt, end_dt)

        # Assertions
        self.assertEqual(result, [])  # No results due to KeyError
#        mock_logger.error.assert_called_once_with("Key: 'games', missing from Game response")


class TestLoadRefereesAssignors(TestCase):
    def setUp(self):
        # Set up an instance of the class that contains get_assignors
        self.instance = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        self.instance.token = 1234  # simulate no token
        self.instance.site_id = 123  # simulate no site_id

    @patch.object(Assignr, 'get_requests')
    def test_successful_response(self,mock_get_requests):
  
        # Mock setup
        mock_get_requests.return_value = (200, {
            'page': {'pages': 1},
            '_embedded': {
                'users': [
                    {'id': '1', 'official': True, 'assignor': False, 'first_name': 'John', 'last_name': 'Doe', 'email_addresses': ['john.doe@example.com']},
                    {'id': '2', 'official': False, 'assignor': True, 'first_name': 'Jane', 'last_name': 'Smith', 'email_addresses': ['jane.smith@example.com']}
                ]
            }
        })

        self.instance.load_referees_assignors()

        # Assertions
        self.assertEqual(len(self.instance.referees), 1)
        self.assertEqual(len(self.instance.assignors), 1)
        self.assertEqual(self.instance.referees['1']['first_name'], 'John')
        self.assertEqual(self.instance.assignors['2']['last_name'], 'Smith')

    @patch.object(Assignr, 'get_requests')
    def test_failed_api_call(self, mock_get_requests):
        
        # Simulate API call failure
        mock_get_requests.return_value = (500, None)

        self.instance.load_referees_assignors()

        # Assertions
        self.assertEqual(self.instance.referees, {})
        self.assertEqual(self.instance.assignors, {})

    @patch.object(Assignr, 'get_requests')
    def test_key_error_in_response(self, mock_get_requests):

        # Simulate missing keys in the response
        mock_get_requests.return_value = (200, {
            'page': {'pages': 1},  # Missing '_embedded' and 'users'
        })

        self.instance.load_referees_assignors()

        # Assertions
        self.assertEqual(self.instance.referees, {})
        self.assertEqual(self.instance.assignors, {})


class TestGetReports(TestCase):
    def setUp(self):
        # Set up an instance of the class that contains get_assignors
        self.instance = Assignr('123', '234', '345', BASE_URL,
                       AUTH_URL)
        self.instance.token = 123
        self.instance.site_id = 333

    @patch.object(Assignr, 'get_requests')
    @patch('helpers.helpers.process_game_report')
    @patch('helpers.helpers.get_coaches_name')
    def test_successful_report_retrieval(self, mock_get_coaches_name, mock_process_game_report,
                                         mock_get_requests):
        # Mock the process_game_report to return a simple dictionary
        mock_process_game_report.side_effect = lambda x: x
        
        mock_get_coaches_name.return_value = {}

        # Mock the API response for get_requests
        with open(join(response_file_dir, f"{sys._getframe(  ).f_code.co_name}.json")) as file:
            get_request_results = json.load(file)

        mock_get_requests.return_value = (200,get_request_results)
        
        start_dt = '2023-09-23'
        end_dt = '2023-09-24'
        assignors = {'Some League': ['assignor1@example.com']}
        coaches = {}

        # Call the function
        result = self.instance.get_reports(start_dt, end_dt, assignors, coaches)

        # Check that the reports structure is correct
        self.assertIn('misconducts', result)
        self.assertIn('admin_reports', result)
        self.assertIn('assignor_reports', result)

    @patch.object(Assignr, 'get_requests')
    def test_api_failure(self,mock_get_requests):
        # Mock the API response to simulate failure
        mock_get_requests.return_value = (500, {})

        start_dt = '2023-09-23'
        end_dt = '2023-09-24'
        assignors = {}
        coaches = {}

        # Call the function
        with self.assertLogs(level='INFO') as cm:
            result = self.instance.get_reports(start_dt, end_dt, assignors, coaches)

        # Check that reports are empty
        self.assertEqual(result['misconducts'], [])
        self.assertEqual(result['admin_reports'], [])
        self.assertEqual(result['assignor_reports'], [])
        self.assertEqual(cm.output, ["ERROR:root:Failed to get reports: 500"])

    @patch.object(Assignr, 'get_requests')
    def test_key_error_in_response(self, mock_get_requests):
        # Mock the API response with missing keys
        mock_get_requests.return_value = (200, {
            'page': {'pages': 1},
            '_embedded': {
                'form_submissions': [
                    {
                        '_embedded': {}  # Missing expected keys
                    }
                ]
            }
        })

        start_dt = '2023-09-23'
        end_dt = '2023-09-24'
        assignors = {}
        coaches = {}

        # Call the function
        with self.assertLogs(level='INFO') as cm:
            result = self.instance.get_reports(start_dt, end_dt, assignors, coaches)

        # Check that reports are still initialized as empty
        self.assertEqual(result['misconducts'], [])
        self.assertEqual(result['admin_reports'], [])
        self.assertEqual(result['assignor_reports'], [])
        self.assertEqual(cm.output, ["ERROR:root:Key: 'values', missing from Game Report response"])
