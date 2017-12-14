import json

from copy import deepcopy
from typing import List

from mdstudio.api.sort_mode import SortMode
from mdstudio.collection import merge_dicts
from mdstudio.db.model import Model
from mdstudio.logging.log_type import LogType
from mdstudio.utc import now


class LogRepository(object):
    class Logs(Model):
        """
        {
            'level': <level>,
            'source': <tags>,
            'message': <message>,
            'time': <time>,
            'createdAt': <createdAt>,
            'createdBy': <claims>
        }
        """
        date_time_fields = ['time', 'createdAt']

    def __init__(self, db):
        self.db = db

    def insert(self, claims, logs):
        # type: (dict, List[dict]) -> List[str]

        n = now()
        logs = deepcopy(logs)
        for i, l in enumerate(logs):
            logs[i]['createdAt'] = n
            logs[i]['createdBy'] = claims
        return self.logs(claims).insert_many(logs)

    def get(self, filter, meta, claims):

        if not meta:
            meta = {
                'request': json.dumps(filter),
                'pageSize': 50,
                'sortMode': str(SortMode.Desc)
            }

        if 'fromId' in meta:
            merge_dicts(filter, {
                '_id': {
                    '$gte': meta['fromId'],
                    '$lte': meta['lastId']
                }
            })
        elif 'lastId' in meta:
            merge_dicts(filter, {
                '_id': {
                    '$lt': meta['lastId']
                }
            })
        # security fail over
        meta['pageSize'] = min(meta['pageSize'], 100)

        results = self.logs(claims).find_many(filter, **{'limit': meta['pageSize'], 'sort': [('_id', SortMode.from_string(meta['sortMode']))]}).to_list()

        next_meta = deepcopy(meta)
        del next_meta['fromId']
        del next_meta['lastId']
        merge_dicts(next_meta, {
            'lastId': results[len(results) - 1]['_id'],
        })
        prev_meta = deepcopy(meta)
        del prev_meta['fromId']
        del prev_meta['lastId']
        merge_dicts(next_meta, {
            'fromId': results[0]['_id'],
            'lastId': results[len(results) - 1]['_id'],
        })

        return results, prev_meta, next_meta

    def logs(self, claims):
        return self.Logs(self.db, collection=self.get_log_collection_name(claims))

    @staticmethod
    def get_log_collection_name(claims):
        log_type = LogType.from_string(claims['logType'])

        if log_type == LogType.User:
            collection_name = 'users~{user}'.format(user=claims['username'])
        elif log_type == LogType.Group:
            collection_name = 'groups~{group}'.format(group=claims['group'])
        elif log_type == LogType.GroupRole:
            collection_name = 'grouproles~{group}~{group_role}'.format(group=claims['group'], group_role=claims['groupRole'])
        else:
            raise NotImplemented('This distinction does not exist')

        return collection_name
