.. _manual:

Manual Installation
===================
When you want to keep track of the whole environment for yourself, you should follow these
instructions.

Prerequisites
-------------
The only external dependencies are the MongoDB_ NoSQL database
making available the `mongod` MongoDB exacutable in the users path, and the ``nodejs`` package.
For a manual installation, make sure you install:

* MongoDB_ running locally.
* Python_
* nodejs_
* pipenv_

First we need to install npm global dendencies:

* gulp_
* gulp-cli_
* typescript_
* typings_

We install them by running:

.. code-block:: bash

    $ npm i -g gulp gulp-cli typescript typings


Installation
------------
Run the ``installer.sh`` script as:

.. code-block:: bash

    $ ./installer.sh -s

for a quick install using the default Python version. Use -h for more information on
customizing the installation.

A quick install will in sequence:

* Setup a python virtual environment (including installation of a local pip and pipenv_)
* Install required packages from the Python package repository.
* Install LIEStudio component Python packages and their dependencies
* Create a self-signed certificate for WAMP communication over TLS secured websockets.
  Certificate creation requires OpenSSL. If not available the default certificate
  shipped with the package will be used (liestudio/data/crossbar).
  It is recommended to replace the certificate with a personal one signed by a offical
  certificate authority when using the application in a production environment.
* Compile API documentation available from the browser when the program is running at
  http://localhost/help.
  
Usage
-----
The application is started on the command line as:

.. code-block:: bash

    $ pipenv run python .

.. _gulp: http://gulpjs.com/
.. _gulp-cli: https://github.com/gulpjs/gulp-cli
.. _typescript: https://www.typescriptlang.org/
.. _typings: https://github.com/typings/typings


.. _Docker: https://www.docker.com/
.. _MongoDB: https://www.mongodb.com
.. _pipenv: https://github.com/kennethreitz/pipenv_
.. _Python: https://www.python.org/download/releases/2.7/
.. _nodejs: https://nodejs.org/en/