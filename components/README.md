# LIEStudio components

Most of the functionality of the LIEStudio application is arranged as a
number of independent Python modules that are installed in the LIEStudio
virtual environment during application setup by the installer.sh script.

The ~/LIEStudio/components directory contains the Python packages for 
these modules that are installed using pip by the LIEStudio installer
script. Any package dependencies will be resolved automatically.

## UnitTesting the components
Each component package contains a `tests` directory with a number of
Python unittests. After activating the virtual environment, they can be 
run as:

    python tests/
  
Some of the component functions require access to a (running) MongoDB
process via PyMongo. If such a process is not active or cannot be 
activated by the lie_db drivers, the unittests for these functions are
scipped.