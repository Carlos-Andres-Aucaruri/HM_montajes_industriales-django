from django.test import TestCase
from datetime import datetime, timedelta
from .models import SettlementDetails

class SettlementDetailsTestCase(TestCase):
    def test_classify_hours(self):
        settlement_details = SettlementDetails()
        list_of_dates = [
            {
                'start_date': datetime.strptime('26/feb/2024 06:30', '%d/%b/%Y %H:%M'),
                'end_date': datetime.strptime('26/feb/2024 18:00', '%d/%b/%Y %H:%M')
            },
            {
                'start_date': datetime.strptime('27/feb/2024 06:30', '%d/%b/%Y %H:%M'),
                'end_date': datetime.strptime('27/feb/2024 18:00', '%d/%b/%Y %H:%M')
            },
            {
                'start_date': datetime.strptime('28/feb/2024 06:30', '%d/%b/%Y %H:%M'),
                'end_date': datetime.strptime('28/feb/2024 18:00', '%d/%b/%Y %H:%M')
            },
            {
                'start_date': datetime.strptime('29/feb/2024 06:30', '%d/%b/%Y %H:%M'),
                'end_date': datetime.strptime('29/feb/2024 18:00', '%d/%b/%Y %H:%M')
            },
            {
                'start_date': datetime.strptime('01/mar/2024 06:00', '%d/%b/%Y %H:%M'),
                'end_date': datetime.strptime('01/mar/2024 15:00', '%d/%b/%Y %H:%M')
            },
            # {
            #     'start_date': datetime.strptime('02/mar/2024 06:00', '%d/%b/%Y %H:%M'),
            #     'end_date': datetime.strptime('02/mar/2024 14:00', '%d/%b/%Y %H:%M')
            # },
            # {
            #     'start_date': datetime.strptime('03/mar/2024 06:00', '%d/%b/%Y %H:%M'),
            #     'end_date': datetime.strptime('03/mar/2024 14:00', '%d/%b/%Y %H:%M')
            # },
        ]
        for date in list_of_dates:
            settlement_details.classify_hours(date['start_date'], date['end_date'], date['start_date'], date['end_date'])
        settlement_details.set_total_hours()

        self.assertEqual(settlement_details.monday, 10.5)
        self.assertEqual(settlement_details.tuesday, 10.5)
        self.assertEqual(settlement_details.wednesday, 10.5)
        self.assertEqual(settlement_details.thursday, 10.5)
        self.assertEqual(settlement_details.friday, 8.0)
        self.assertEqual(settlement_details.saturday, 0.0)
        self.assertEqual(settlement_details.sunday, 0.0)

        # Comprueba que las horas totales son correctas
        self.assertEqual(settlement_details.total_hours, 50.0)
        self.assertEqual(settlement_details.ordinary_hours, 47.0)
        self.assertEqual(settlement_details.daytime_overtime, 3.0)
        self.assertEqual(settlement_details.night_surcharge_hours, 0.0)
        self.assertEqual(settlement_details.night_overtime, 0.0)
        self.assertEqual(settlement_details.holiday_hours, 0.0)
        self.assertEqual(settlement_details.night_holiday_hours, 0.0)
        self.assertEqual(settlement_details.daytime_holiday_overtime, 0.0)
        self.assertEqual(settlement_details.night_holiday_overtime, 0.0)