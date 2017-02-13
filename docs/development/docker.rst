.. _docker:

Docker Installation
===================
To make development easier we have setup a docker environment.

Prerequisites
-------------

 * Docker_, that's it.

Usage
-----
To use the docker environment you have to start the container:

.. code-block:: bash

    $ ./start.sh

After this we login to our docker container and we can start LIEStudio with:

.. code-block:: bash

    $ python .

This command will spin up the complete environment including MongoDB, and ssh's into the 
container. When you want to exit this mode just use `>> exit` to exit. Containers can be
stopped using:

.. code-block:: bash

    $ ./stop.sh

SSH Access
----------
When you want to use your private shell you can login using ssh using the following setttings:

+--------+----------------------------------+
| Host   | ``127.0.0.1``                    |
+--------+----------------------------------+
| Key    | ``docker/insecure_id_rsa.ppk``   |
+--------+----------------------------------+
| User   | ``root``                         |
+--------+----------------------------------+
| Port   | ``65432``                        |
+--------+----------------------------------+

.. warning::

    On Windows it could be that the working directory is empty. Please use ``cd /app`` to go to the correct directory!

IDE Integration
---------------

Pycharms
--------

Go to `File > Project Settings > Project Interpreter`, and add a remote interpreter,
and make sure it matches this screen.

.. image:: ../img/pycharm-config.png

Note specifically:

+--------------------+------------------------------+
| Interpreter path   | ``/app/.venv/bin/python``    |
+--------------------+------------------------------+
| Pycharm helpers    | ``/app/.pycharm_helpers``    |
+--------------------+------------------------------+

Debug Hook
----------
While we now support breakpoints and the likes natively, Pycharm still fails to do post morten
debugging in components. Fixing this is easy; We go to `Run > View Breakpoints`. We add a 
python exception breakpoint. 

.. image:: ../img/pycharm-breakpoint.png

After that we select the runpy._error exception:

.. image:: ../img/pycharm-error.png

Make sure `On Raise` is selected:

.. image:: ../img/pycharm-raise.png