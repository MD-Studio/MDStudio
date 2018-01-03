
import json
import yaml

from run_parameters.run_composer import RunInput
from gromacs.mdp_generator import GenerateMdp

def main():

    with open("/app/components/lie_md-0.1/lie_md/template/mdstudio_1.0.mdtp") as ifs:
        
        run_input = RunInput( ifs )
        run_file = run_input.Compose(["run_properties", "center_of_mass", "minimization"])

        run_file.run_properties.integrator = "leap-frog"
        run_file.run_properties.start_time = 0.0
        run_file.run_properties.delta_time = 0.002
        run_file.run_properties.steps      = 2000
        run_file.run_properties.seed       = 1991

        run_file.center_of_mass.mode       = "linear"
        run_file.center_of_mass.frequency  = 100

        run_file.minimization.tolerance    = 10.0
        run_file.minimization.step_size    = 0.01
        run_file.minimization.steps        = 1000

        

        GenerateMdp( run_file, "2016.3", None)

if __name__ == '__main__':

    main()

