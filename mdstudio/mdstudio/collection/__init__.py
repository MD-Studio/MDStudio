import collections


def merge_dicts(a, b):
    for k, v in b.items():
        if k in a and isinstance(a[k], dict) and isinstance(b[k], collections.Mapping):
            merge_dicts(a[k], b[k])
        else:
            a[k] = b[k]
