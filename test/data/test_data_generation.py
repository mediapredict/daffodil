from datetime import datetime, timezone, timedelta
from random import randint


now = datetime.now().replace(tzinfo=timezone.utc)
day_start = now.replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=timezone.utc)


def random_until_now(start):
    return randint(int(start.timestamp()), int(now.timestamp()))


def days_ago_ts(days):
    return (now - timedelta(days=days)).timestamp()


days_ago_0 = random_until_now(day_start)
days_ago_3 = days_ago_ts(3)

weeks_ago_0 = random_until_now(
    (day_start - timedelta(days=day_start.weekday()))
)
weeks_ago_5 = days_ago_ts(7 * 5)

months_ago_0 = random_until_now(day_start.replace(day=1))
months_ago_7 = days_ago_ts(7 * 30)

years_ago_0 = random_until_now(day_start.replace(month=1, day=1))
years_ago_2 = days_ago_ts(2 * 365)
