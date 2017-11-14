import pytz
import datetime

from dateutil.parser import parse as parsedate

def now():
    # type: () -> datetime
    return datetime.datetime.now(tz=pytz.utc)


def to_utc_string(datetime):
    # type: (datetime) -> str
    return datetime.isoformat()

def from_utc_string(datetime):
    # type: (str) -> datetime
    return parsedate(datetime).astimezone(pytz.utc)
