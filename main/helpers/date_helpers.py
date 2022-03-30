import time
import datetime
from dateutil.parser import parse
import pandas as pd


class Time_Manipulator:
    @staticmethod
    def get_months_before(end_month, num_months=6):
        """ "Function takes a date and returns the date and six months before that date"""

        today = end_month  # datetime.date.today()

        for i in range(6):

            first = today.replace(day=1)
            lastMonth = first - datetime.timedelta(days=1)
            lastMonth = lastMonth.replace(day=1)

            today = lastMonth

        start_month = today

        return start_month, end_month

    @staticmethod
    def generate_months_between_dates(start_date, end_date):

        months = [
            datetime.datetime.strptime("%2.2d-%2.2d" % (y, m), "%Y-%m").strftime(
                "%m-%Y"
            )
            for y in range(start_date.year, end_date.year + 1)
            for m in range(
                start_date.month if y == start_date.year else 1,
                end_date.month + 1 if y == end_date.year else 13,
            )
        ]

        return months

    @staticmethod
    def generate_days_between_dates(start_date, end_date):

        period_df = pd.Series(pd.date_range(start=start_date, end=end_date)).dt.date

        return period_df

    @staticmethod
    def convert_date_format(drf_type_date) -> str:
        print("-----------------_______________---------------")
        print(drf_type_date)
        """CONVERTS DATE TIME FORMAT (2019-10-19 00:00:00+00:00) -> (11-06-2020 10:16:18+0000).
            FOR DJANGO REST FRAME WORK TO REMITA REQUIRED TIME FORMAT"""

        drf_type_date_object = datetime.datetime.strptime(
            drf_type_date, "%Y-%m-%d %H:%M:%S+00:00"
        )
        remita_acceptable_date_time = drf_type_date_object.strftime(
            "%d-%m-%Y %H:%M:%S+0000"
        )

        return remita_acceptable_date_time
