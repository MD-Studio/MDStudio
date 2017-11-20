from datetime import datetime, date

from mdstudio.utc import to_utc_string, to_date_string


def convert_obj_to_json(document):
    if isinstance(document, dict):
        iter = document.items()
    elif isinstance(document, list):
        iter = enumerate(document)
    else:
        return

    for key, value in iter:
        if isinstance(value, datetime):
            document[key] = to_utc_string(value)
        elif isinstance(value, date):
            document[key] = to_date_string(value)
        else:
            convert_obj_to_json(value)
