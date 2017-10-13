# coding=utf-8


class Collection(dict):
    # type: str
    name = None
    # type: str
    namespace = None

    def __init__(self, name, namespace):
        # type: (str, str) -> None
        self.name = name
        self.namespace = namespace

        dict.__init__(self, name=name, namespace=namespace)
