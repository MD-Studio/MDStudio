import json

class TopologyEncoder(json.JSONEncoder):
    def default(self, obj):
        print( obj )