from pprint import pprint

from mdstudio.api.endpoint import endpoint
from mdstudio.component.session import ComponentSession
from mdstudio.deferred.call_later import call_later
from mdstudio.deferred.chainable import chainable
from mdstudio.utc import now, from_utc_string


class EchoComponent(ComponentSession):
    @endpoint('mdgroup.echo.endpoint.hello', 'hello-request', 'hello-response')
    def hello(self, request, claims):
        return_time = now()
        request['message']['sendTime'] = send_time = from_utc_string(request['message']['sendTime'])

        if self.component_config.settings['printInEndpoint']:
            pprint(request)

        self.report_delay('User -> Component', return_time - send_time)

        request['returnTime'] = return_time

        return request

    def on_run(self):
        @chainable
        def later(self=self):
            with self.group_context('mdgroup'):
                send_time = now()
                response = yield self.call('mdgroup.echo.endpoint.hello', {
                    'message': {
                        'greeting': 'Hello World!',
                        'sendTime': send_time
                    }
                })

            response['returnTime'] = return_time = from_utc_string(response['returnTime'])
            receive_time = now()
            self.report_delay('Component -> User', receive_time - return_time)
            self.report_delay('Total', receive_time - send_time)

        call_later(2, later)
        print('Waiting a few seconds for things to start up')

    def authorize_request(self, uri, claims):
        # If you were allowed to call this in the first place, I will assume you are authorized
        return True

    def report_delay(self, direction, delay):
        self.log.info('{direction:>20} delay: {delay:>8.2f} ms', direction=direction, delay=delay.total_seconds() * 1000)

