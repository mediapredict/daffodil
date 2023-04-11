from datetime import datetime, timedelta
from random import randint

from dateutil.relativedelta import relativedelta


now = datetime.now()
day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)


def random_until_now(start):
    return randint(int(start.timestamp()), int(now.timestamp()))


def offset_to_ts(days=0, weeks=0, months=0, years=0):
    return (
        now - relativedelta(days=days, weeks=weeks, months=months, years=years)
    ).timestamp()


days_ago_0 = random_until_now(day_start)
days_ago_3 = offset_to_ts(3)

weeks_ago_0 = random_until_now(
    (day_start - timedelta(days=day_start.weekday()))
)
weeks_ago_5 = offset_to_ts(weeks=5)

months_ago_0 = random_until_now(day_start.replace(day=1))
months_ago_7 = offset_to_ts(months=7)

years_ago_0 = random_until_now(day_start.replace(month=1, day=1))
years_ago_2 = offset_to_ts(years=2)
