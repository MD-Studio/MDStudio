from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main
from os.path import join
import os
import shutil

residues = [28, 29, 65, 73, 74]
workdir = "/tmp/structures"
if os.path.exists(workdir):
    shutil.rmtree(workdir)


class Run_structures(ComponentSession):

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):
        with self.group_context('mdgroup'):
            toolkits = yield self.call(
                "mdgroup.lie_structures.endpoint.supported_toolkits",
                {})
            print(toolkits)


if __name__ == "__main__":
    main(Run_structures)
