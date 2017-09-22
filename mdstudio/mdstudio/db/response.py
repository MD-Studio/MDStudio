# coding=utf-8


class UpdateManyResponse:
    # type: int
    matched_count = 0
    # type: int
    modified_count = 0
    # type: str
    upserted_id = None

    def __init__(self, response):
        # type: (dict) -> None
        self.matched_count = response['matched']
        self.modified_count = response['modified']
        self.upserted_id = response.get('upsertedId')


class UpdateOneResponse:
    # type: int
    matched_count = 0
    # type: int
    modified_count = 0
    # type: str
    upserted_id = None

    def __init__(self, response):
        # type: (dict) -> None
        self.matched_count = response['matched']
        self.modified_count = response['modified']
        self.upserted_id = response.get('upsertedId')


class ReplaceOneResponse:
    # type: int
    matched_count = 0
    # type: int
    modified_count = 0
    # type: str
    upserted_id = None

    def __init__(self, response):
        # type: (dict) -> None
        self.matched_count = response['matched']
        self.modified_count = response['modified']
        self.upserted_id = response.get('upsertedId')
