from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main
import os
import shutil

workdir = "/tmp/pylie"
if os.path.exists(workdir):
    shutil.rmtree(workdir)


class Run_pylie(ComponentSession):

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):
        with self.group_context('mdgroup'):
            result_collect = self.call(
                "mdgroup.lie_pylie.endpoint.collect_energy_trajectories",
                {"workdir": workdir})

            result_stable = self.call(
                "mdgroup.lie_pylie.endpoint.filter_stable_trajectory",
                {"workdir": workdir})

            result_average = self.call(
                "mdgroup.lie_pylie.endpoint.calculate_lie_average",
                {"workdir": workdir})

            result_liedeltag = self.call(
                "mdgroup.lie_pylie.endpoint.liedeltag",
                {"workdir": workdir})

            result_similarity = self.call(
                "mdgroup.lie_pylie.endpoint.chemical_similarity",
                {"workdir": workdir})


if __name__ == "__main__":
    main(Run_pylie)
