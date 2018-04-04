from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main
from os.path import join
import os
import shutil

workdir = "/tmp/amber"
amber_input = join(workdir, "input.mol2")
if os.path.exists(workdir):
    shutil.rmtree(workdir)


class Run_acpype(ComponentSession):

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):
        with self.group_context('mdgroup'):
            self.call(
                "mdgroup.lie_amber.endpoint.acpype",
                {"structure": amber_input,
                 "workdir": workdir,
                 "from_file": True})


if __name__ == "__main__":
    main(Run_acpype)





