from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main
import os
import shutil

workdir = "/tmp/mdstudio/lie_amber"
structure_path = os.path.join(os.getcwd(), "input.mol2")
with open(structure_path, 'r') as f:
    amber_input = f.read()


class Run_acpype(ComponentSession):

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):
        with self.group_context('mdgroup'):
            result = yield self.call(
                "mdgroup.lie_amber.endpoint.acpype",
                {"structure": amber_input,
                 "workdir": workdir,
                 "from_file": False})
            print(result)


if __name__ == "__main__":
    main(Run_acpype)
