from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main
import os
import shutil

workdir = "/tmp/propka"
if os.path.exists(workdir):
    shutil.rmtree(workdir)


class Run_propka(ComponentSession):

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):
        with self.group_context('mdgroup'):
            self.call(
                "mdgroup.lie_propka.endpoint.propka",
                {"workdir": workdir})


if __name__ == "__main__":
    main(Run_propka)
