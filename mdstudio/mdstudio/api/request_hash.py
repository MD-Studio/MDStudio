import json
from base64 import b64encode
from hashlib import sha512
import copy

from mdstudio.api.converter import convert_obj_to_json

def request_hash(request):
    request = convert_obj_to_json(copy.deepcopy(request))
    return b64encode(sha512(json.dumps(request, sort_keys=True).encode('utf8')).digest()).decode('utf8')