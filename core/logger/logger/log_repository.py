from typing import List

from copy import deepcopy

from mdstudio.api.claims import whois
from mdstudio.api.context import ContextCallable
from mdstudio.api.paginate import paginate_cursor
from mdstudio.service.model import Model
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value
from mdstudio.logging.log_type import LogType
from mdstudio.utc import now


class LogRepository(ContextCallable):
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
        super(LogRepository, self).__init__()

    def insert(self, claims, logs, tags=None):
        # type: (dict, List[dict]) -> List[str]

        if not tags:
            tags = ['logs']

        n = now()
        logs = deepcopy(logs)
        for i, l in enumerate(logs):
            logs[i]['createdAt'] = n
            logs[i]['createdBy'] = whois(claims, 'logType')
            logs[i]['tags'] = tags
        return self.logs(claims).insert_many(logs)

    @chainable
    def get(self, filter, claims, **kwargs):
        results, prev_meta, next_meta = yield self.logs(claims).paginate.find_many(filter, **kwargs)

        for o in results:
            del o['_id']

        return_value((results, prev_meta, next_meta))

    def logs(self, claims):
        return self.Logs(self.db, collection=self.get_log_collection_name(claims))(self.call_context)

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
