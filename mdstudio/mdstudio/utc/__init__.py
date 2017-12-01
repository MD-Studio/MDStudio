from datetime import datetime, date

import pytz
from dateutil.parser import parse as parsedate


def now():
    # type: () -> datetime
    return datetime.now(tz=pytz.utc)


def today():
    # type: () -> date
    return datetime.now(tz=pytz.utc).date()


def to_utc_string(ldatetime):
    # type: (ldatetime) -> str
    return ldatetime.astimezone(pytz.utc).isoformat()


def to_date_string(ldate):
    # type: (ldate) -> str
    return ldate.isoformat()


def from_utc_string(dt):
    # type: (str) -> datetime
    parsed = parsedate(dt)
    # fix for python < 3.6
    if not parsed.tzinfo:
        parsed = parsed.replace(tzinfo=pytz.utc)
    return parsed.astimezone(pytz.utc)


def from_date_string(ldate):
    # type: (str) -> ldate
    parsed = parsedate(ldate)
    # fix for python < 3.6
    if not parsed.tzinfo:
        parsed = parsed.replace(tzinfo=pytz.utc)
    return parsed.astimezone(pytz.utc).date()
