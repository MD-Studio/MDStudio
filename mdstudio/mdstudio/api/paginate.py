import json
from typing import Tuple, List, Optional, Callable

from copy import deepcopy

from mdstudio.api.sort_mode import SortMode
from mdstudio.collection import merge_dicts
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value


@chainable
def paginate_cursor(filter, func, meta=None, paging=None, **kwargs):
    # type: (dict, Callable[dict, dict], Optional[Callable], Optional[dict], Optional[dict]) -> Tuple[List[dict], Optional[dict], Optional[dict]]
    allow_prev = True
    direction = SortMode.Desc
    if not meta:
        meta = {
            'request': json.dumps(filter),
            'limit': 50
        }
        if 'limit' in paging:
            meta['limit'] = paging['limit']

        allow_prev = False
        if paging or isinstance(paging, dict):
            meta['page'] = 1

    if 'first' in meta:
        merge_dicts(filter, {
            '_id': {
                '$lt': meta['first']
            }
        })
    elif 'last' in meta:
        merge_dicts(filter, {
            '_id': {
                '$gt': meta['last']
            }
        })
        direction = SortMode.Asc
    # security fail over and add one extra to check if alive
    meta['limit'] = min(meta['limit'] + 1, 101)

    results = yield func(filter, **{
        'meta': meta,
        'paging': paging,
        'db': {
            'limit': meta['limit'],
            'sort': [('_id', direction)]
        },
        'kwargs': kwargs
    })

    alive = len(results) == meta['limit']

    meta['limit'] -= 1
    results = results[:meta['limit'] if alive else len(results)]
    if 'first' in meta:
        results.reverse()

    next_meta = deepcopy(meta)
    prev_meta = deepcopy(meta)
    next_meta.pop('first', None)
    next_meta.pop('last', None)
    prev_meta.pop('first', None)
    prev_meta.pop('last', None)
    if alive or 'last' in meta:
        next_meta['last'] = results[len(results) - 1]['_id']
        if 'page' in next_meta:
            next_meta['page'] = meta['page'] + 1
    else:
        next_meta = None
    if allow_prev and (alive or 'first' in meta):
        prev_meta['first'] = results[0]['_id']
        if 'page' in prev_meta:
            prev_meta['page'] = meta['page'] - 1
    else:
        prev_meta = None

    return_value((results, prev_meta, next_meta))
