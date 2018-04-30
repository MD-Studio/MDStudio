from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main
from mdstudio.utc import now
import json


msg = {"message":
       {"greeting": "Hoi!",
        "sendTime": now()}}


class Run_md(ComponentSession):

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):
        with self.group_context('mdgroup'):
            r = yield self.call(
                "mdgroup.echo.endpoint.hello",
                msg)
        with open("/tmp/echo.json", "w") as f:
            json.dump(r, f)


if __name__ == "__main__":
    main(Run_md)