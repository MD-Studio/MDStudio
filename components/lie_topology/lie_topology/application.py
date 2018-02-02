from pprint import pprint

from mdstudio.api.endpoint import endpoint
from mdstudio.component.session import ComponentSession
from mdstudio.deferred.call_later import call_later
from mdstudio.deferred.chainable import chainable
from mdstudio.utc import now, from_utc_string

class TopologyComponent(ComponentSession):
    @endpoint('parse-structure', 'structure-request', 'structure-response')
    def parseStructure(self, request, claims):
        
        return { "system": {
                    "groups" : [   
                        {
                            "uid": "G0x01",
                            "name": "chain_A",
                            "molecules": [
                                {
                                    "uid": "M0x01",
                                    "name": "TYR",
                                    "atoms": [
                                        {
                                            "uid": "A0x01",
                                            "name": "CA",
                                            "element": "C"
                                        },
                                        {
                                            "uid": "A0x02",
                                            "name": "CB",
                                            "element": "C"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                 }
            }

    @endpoint('test-response', 'tti', 'tto')
    def reponseTiming(self, request, claims):
        
        return_time = now()
        send_time = from_utc_string(request['message']['sendTime'])
        request['message']['sendTime'] = send_time

        pprint(request)
        self.report_delay('User -> Component', return_time - send_time)

        request['returnTime'] = return_time

        return request

    def on_run(self):
        call_later(2, self.is_alive)
        print('Waiting a few seconds for things to start up')

    def authorize_request(self, uri, claims):
        # If you were allowed to call this in the first place, I will assume you are authorized
        return True

    @chainable
    def is_alive(self):
        send_time = now()
        response = yield self.call('mdgroup.topology.endpoint.test-response', {
            'message': {
                'greeting': 'Hello World!',
                'sendTime': send_time
            }
        })
        response['returnTime'] = return_time = from_utc_string(response['returnTime'])
        receive_time = now()
        self.report_delay('Component -> User', receive_time - return_time)
        self.report_delay('Total', receive_time - send_time)

        response2 = yield self.call('mdgroup.topology.endpoint.parse-structure', {
            "format": "pdb",
            "data": ""
        })

        self.log.info(response2["system"])


    def report_delay(self, direction, delay):
        self.log.info('{direction:>20} delay: {delay:>8.2f} ms', direction=direction, delay=delay.total_seconds() * 1000)

