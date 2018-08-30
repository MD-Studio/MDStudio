from datetime import datetime, date

from mdstudio.utc import to_utc_string, to_date_string


def convert_obj_to_json(document):
    if isinstance(document, bytes):      
        return document.decode('utf-8')
    if isinstance(document, (str, int)): 
        return str(document)
    if isinstance(document, dict):       
        return dict(map(convert_obj_to_json, document.items()))
    if isinstance(document, tuple):      
        return tuple(map(convert_obj_to_json, document))
    if isinstance(document, list):       
        return list(map(convert_obj_to_json, document))
    if isinstance(document, set):        
        return set(map(convert_obj_to_json, document))
    if isinstance(document, date) and not isinstance(document, datetime):
        return to_date_string(document)
    if isinstance(document, datetime):
        return to_utc_string(document)