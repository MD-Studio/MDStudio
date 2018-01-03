import json
from base64 import b64encode
from hashlib import sha512


def request_hash(request):
    return b64encode(sha512(json.dumps(request, sort_keys=True).encode('utf8')).digest()).decode('utf8')