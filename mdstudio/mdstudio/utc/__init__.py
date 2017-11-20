import pytz
from datetime import datetime, date

from dateutil.parser import parse as parsedate


def now():
    # type: () -> datetime
    return datetime.now(tz=pytz.utc)


def to_utc_string(datetime):
    # type: (datetime) -> str
    return datetime.astimezone(pytz.utc).isoformat()


def to_date_string(date):
    # type: (date) -> str
    return date.isoformat()


def from_utc_string(datetime):
    # type: (str) -> datetime
    return parsedate(datetime).astimezone(pytz.utc)


def from_date_string(date):
    # type: (str) -> date
    return parsedate(datetime).astimezone(pytz.utc).date
