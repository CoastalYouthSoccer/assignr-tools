from datetime import (datetime, timedelta)
from unittest import TestCase
from misconduct import get_arguments

ERROR_USAGE='ERROR:misconduct:USAGE: misconduct.py -s <start-date>' \
    ' -e <end-date> DATE FORMAT=MM/DD/YYYY'
DATE_01012020 = '01/01/2020'
DATE_01012021 = '01/01/2021'
DATE_FORMAT_01012020 = datetime.strptime(DATE_01012020, "%m/%d/%Y").date()
DATE_FORMAT_01012021 = datetime.strptime(DATE_01012021, "%m/%d/%Y").date()
class TestGetArguments(TestCase):
    def test_help(self):
        expected_args = {'start_date': None, 'end_date': None}
        with self.assertLogs(level='INFO') as cm:
            rc, args = get_arguments(['-h'])
        self.assertEqual(cm.output, [ERROR_USAGE])
        self.assertEqual(rc, 99)
        self.assertEqual(args, expected_args)

    def test_valid_options(self):
        expected_args = {
            'start_date': DATE_FORMAT_01012020,
            'end_date': DATE_FORMAT_01012021
        }
        rc, args = get_arguments(['-s', DATE_01012020, '-e', DATE_01012021])
        self.assertEqual(rc, 0)
        self.assertEqual(args, expected_args)

    def test_invalid_options(self):
        expected_args = {'start_date': None, 'end_date': None}
        with self.assertLogs(level='INFO') as cm:
            rc, args = get_arguments(['-n'])
        self.assertEqual(cm.output, [ERROR_USAGE])
        self.assertEqual(rc, 77)
        self.assertEqual(args, expected_args)

    def test_missing_start_date(self):
        start_date = DATE_FORMAT_01012020 - timedelta(days=7)

        expected_args = {
            'start_date': start_date,
            'end_date': DATE_FORMAT_01012020
        }
        with self.assertLogs(level='INFO') as cm:
            rc, args = get_arguments(['-e', DATE_01012020])
        self.assertEqual(cm.output, [
            'INFO:misconduct:End Date set to 2020-01-01',           
            f'INFO:misconduct:No start date provided, setting to {start_date}',
            f'INFO:misconduct:Start Date set to {start_date}'
            ])
        self.assertEqual(rc, 0)
        self.assertEqual(args, expected_args)

    def test_missing_end_date(self):
        end_date = datetime.now().date()
        expected_args = {
            'start_date': DATE_FORMAT_01012020,
            'end_date': end_date
        }
        with self.assertLogs(level='INFO') as cm:
            rc, args = get_arguments(['-s', DATE_01012020])
        self.assertEqual(cm.output, [
            f'INFO:misconduct:No end date provided, setting to {end_date}',
            f'INFO:misconduct:End Date set to {end_date}',
            'INFO:misconduct:Start Date set to 2020-01-01'
        ])
        self.assertEqual(rc, 0)
        self.assertEqual(args, expected_args)

    def test_start_date_greater_end_date(self):
        end_date = datetime.strptime(DATE_01012020, "%m/%d/%Y").date()
        start_date = datetime.strptime('01/10/2020', "%m/%d/%Y").date()
        expected_args = {
            'start_date': start_date,
            'end_date': end_date
        }
        with self.assertLogs(level='INFO') as cm:
            rc, args = get_arguments(['-s', '01/10/2020', '-e', DATE_01012020])
        self.assertEqual(cm.output, [
            f'INFO:misconduct:End Date set to {end_date}',
            f'INFO:misconduct:Start Date set to {start_date}',
            f'ERROR:misconduct:Start Date {start_date} is after End Date {end_date}'
        ])
        self.assertEqual(rc, 88)
        self.assertEqual(args, expected_args)