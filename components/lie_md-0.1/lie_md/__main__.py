
import json
import yaml

from run_parameters.run_composer import RunInput

def main():

    with open("/app/components/lie_md-0.1/lie_md/template/mdstudio_revA.mdtp") as ifs:
        
        runInput = RunInput( ifs )
        runfile = runInput.Compose(["system"])
        runfile.system.npm = 1


if __name__ == '__main__':

    main()

