from datetime import datetime
from unittest import TestCase
from unittest.mock import (patch, MagicMock)
from helpers.email import (EMailClient, get_email_components)

CONST_EMAIL = 'test@example.org'
CONST_SUBJECT = 'Test Email'
CONST_NAME = 'Test User'
CONST_SENDER_EMAIL = 'test_sender@example.com'
CONST_SENDER_NAME = 'Test Sender'
CONST_TEMPLATE_TEXT = 'misconduct.text.jinja'
CONST_TEMPLATE_HTML = 'misconduct.html.jinja'
CONST_TEST_MESSAGE = "This is a test message"
CONST_FROM_EMAIL = "Hanover Soccer Referee <test_sender@example.com>"
CONST_START_MESSAGE = "DEBUG:helpers.email:Starting create message ..."
CONST_END_MESSAGE = "DEBUG:helpers.email:Completed create message ..."
CONST_TEST_USER = "test user"
CONST_DATE_FORMAT = "%m/%d/%Y"

CONST_DATA_NO_MESSAGE = {
    'email': CONST_EMAIL,
    'subject': CONST_SUBJECT,
    'name': CONST_NAME
}

CONST_DATA_MESSAGE = {
    'subject': CONST_SUBJECT,
    'content': {
        'misconducts': [{
        "home_team_score": "0",
        "away_team_score": "4",
        "text": "Player #4 Simpson (Springfield) violently struck AR1 in the 43rd minute after an offside was called.\u00a0 Player was sent off.\u00a0 IDK\u00a0awarded yellow team",
        "html": "<div class=\"trix-content\"> <div>Player #4 Simpson (Springfield) violently struck AR1 in the 43rd minute after an offside was called. Player was sent off. IDK awarded yellow team</div> </div>",
        "officials": [{
            "no_show": "false",
            "position": "Referee",
            "first_name": "Mickey",
            "last_name": "Mouse"
        }],
        "author": "Homer Simpson",
        "game_dt": "2023-10-21T09:15:00.000-04:00",
        "home_team": "Springfield-1",
        "away_team": "Ogdenville-1",
        "venue": "Springfield Elementary School",
        "sub_venue": "Field Four",
        "game_type": "Coastal",
        "age_group": "Grade 5/6",
        "gender": "Boys",
        "home_coach": "Mr. Burns",
        "away_coach": "Mr. Smithers" }]
    }
}

mock_email_response = MagicMock()
mock_email_response.status_code = 200
mock_email_response.json.return_value = {
    "token_type": "Bearer",
    "scope": "read",
    "created_at": 1606420331
}


class TestEmailHelpers(TestCase):
    def test_valid_email_components(self):
        expected_result = {
            'name': CONST_TEST_USER,
            'address': 'test@example.org'
        }
        result = get_email_components("test user<test@example.org>")
        self.assertEqual(result, expected_result)

    def test_invalid_email_name(self):
        expected_result = {
            'name': '',
            'address': 'test usertest@example.org'
        }
        result = get_email_components("test usertest@example.org")
        self.assertEqual(result, expected_result)

    def test_invalid_email_address_missing_at(self):
        expected_result = {
            'name': CONST_TEST_USER,
            'address': 'testexample.org'
        }
        result = get_email_components("test user<testexample.org>")
        self.assertEqual(result, expected_result)

    def test_invalid_email_address_missing_dot(self):
        expected_result = {
            'name': CONST_TEST_USER,
            'address': 'test@example'
        }
        result = get_email_components("test user<test@example>")
        self.assertEqual(result, expected_result)

class TestEMail(TestCase):
    def test_send_email_missing_required_fields(self):
        email_client = EMailClient('test', 587, CONST_SENDER_EMAIL,
                                   CONST_SENDER_NAME, 'test_password')

        with self.assertLogs(level='DEBUG') as cm:
            result = email_client.send_email(None, None, None)
        self.assertEqual(result, 22)
        self.assertEqual(cm.output, [
            "DEBUG:helpers.email:Starting send email ...",
            "ERROR:helpers.email:'subject' is required",
            "ERROR:helpers.email:'message' is required",
            "ERROR:helpers.email:'addressee' is required"

        ])

