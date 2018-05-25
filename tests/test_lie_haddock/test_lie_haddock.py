from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main
import os
import shutil


def copy_to_workdir(file_path, workdir):
    shutil.copy(file_path, workdir)
    base = os.path.basename(file_path)
    return os.path.join(workdir, base)


workdir = "/tmp/mdstudio/lie_haddock"
project_file = copy_to_workdir(os.path.join(os.getcwd(), "easy_run_server_ref.web"), workdir)

class Run_haddock(ComponentSession):

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):
        with self.group_context('mdgroup'):
            result = yield self.call(
                "mdgroup.lie_haddock.endpoint.submit_project",
                {"project_id": project_file,
                 "haddock_username": "",
                 "haddock_password": ""})
            print(result['project_id'])


if __name__ == "__main__":
    main(Run_haddock)
