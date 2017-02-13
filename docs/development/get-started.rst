.. _get-started:

Get Started
===========

.. toctree::
    :maxdepth: 2
    
    docker
    manual

To get started with LIEStudio, we should first install the application. 
First install git_, and after that clone LIEStudio:

.. code-block:: bash

    $ git clone https://github.com/NLeSC/LIEStudio.git


We can now choose two options:

    * A :ref:`docker` installation - The most simple and complete installation (recommended)
    * A complete :ref:`manual` installation - A bit harder but more control

Using LIEStudio
---------------
LIEStudio consists of three parts:

 * Backend code based on Crossbar_ written in python.
 * Frontend code based on Angularjs_ written in typescript.
 * The documentation.

Backend
~~~~~~~
LIEStudio runs both the backend, and will spin up a simple webserver to run the frontend.

On docker we run the application with:

.. code-block:: bash

    $ python .

Manually we have to use pipenv:

.. code-block:: bash

    $ pipenv run python .

.. tip::
   The LIEStudio application runs on  `http://localhost:8080/ <http://localhost:8080>`_ or   `http://localhost/ <http://localhost>`_ on docker.

Frontend
~~~~~~~~
The frontend is compiled using ``gulp compile`` in the ``installer.sh``. When there is no active development
on the GUI, this should suffice. However to manually recompile the frontend, you should change the working
directory to ``app``. After this we have two commands:

 * ``gulp serve`` - A live recompilation of Angularjs_, that allows for simple development.
 * ``gulp compile`` - A single compile to bring LIEStudio to the latest version of the GUI.

 .. tip::
   In the docker container you can also use the command ``serve``, which will run ``gulp serve`` from the correct directory for you.
   Also the command ``compile`` is available.

 .. tip::
   To see the live compilation you should go to `http://localhost:5000 <http://localhost:5000>`_.

Documentation
~~~~~~~~~~~~~
The documentation by default is build when LIEStudio is installed. However we can also update and live serve the documentation while
developing. First go to the ``docs`` directory. After this we can either run ``make html`` or ``make livehtml``.

We can also compile the documentation by using the installer:

.. code-block:: bash

    $ ./installer.sh -d

.. tip::
   In the docker container you can also use the command ``livedocs``, which will run the livedocs reloading.
   Also the command ``docs`` is available.

.. tip::
   To see the live documentation you should go to `http://localhost:8000 <http://localhost:8000>`_.


.. _git: https://git-scm.com/
.. _Crossbar: http://crossbar.io
.. _Angularjs: https://angularjs.org/