# coding=utf-8


class UpdateManyResponse(object):
    # type: int
    matched = 0
    # type: int
    modified = 0
    # type: str
    upserted_id = None

    def __init__(self, response):
        # type: (dict) -> None
        self.matched = response['matched']
        self.modified = response['modified']
        self.upserted_id = response.get('upsertedId', None)


class UpdateOneResponse(object):
    # type: int
    matched = 0
    # type: int
    modified = 0
    # type: str
    upserted_id = None

    def __init__(self, response):
        # type: (dict) -> None
        self.matched = response['matched']
        self.modified = response['modified']
        self.upserted_id = response.get('upsertedId', None)


class ReplaceOneResponse(object):
    # type: int
    matched = 0
    # type: int
    modified = 0
    # type: str
    upserted_id = None

    def __init__(self, response):
        # type: (dict) -> None
        self.matched = response['matched']
        self.modified = response['modified']
        self.upserted_id = response.get('upsertedId', None)
