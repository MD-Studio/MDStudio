#!/usr/bin/env python

import json

def to_web(data):
    
    print('HaddockRunParameters (')
    
    def _parse(d, indent=2):
        for k,v in d.items():
            if type(v) == dict:
                print('{0}{1}')
                _parse(v, indent=indent+2)
            else:
                print('{0}{1} = {2},'.format(' '*indent, k, v))
    
    _parse(data)

imp = json.load(open('/Users/mvdijk/Documents/WorkProjects/liestudio-master/liestudio/components/lie_haddock/lie_haddock/tests/files/test.json'))
to_web(imp)

