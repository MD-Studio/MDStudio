###########################
**FOR INTERNAL USAGE ONLY**
###########################

# haddock-xmlrpc-interface

This repository gathers different interfaces to HADDOCK software (http://www.bonvinlab.org/software/haddock2.2/) developed by 
the group of Pr. Alexandre Bonvin at Utrecht University.

The bridge between your local python script/pipeline and the software is made through an XMLRPC API implemented on the server 
side. By setting up a proper XMLRPC server on the client side, you can expose different methods to interact with HADDOCK and 
its environment.

The different methods exposed through the HADDOCKInterface class and accessible to users (in parenthesis the **minimum access level** required to use the function):

* list_projects() => List all projects of a specific user (**EASY**)
* get_status() => Get status of a specific project (**EASY**)
* get_url() => Get URL of a finished project archive (**EASY**)
* get_params() => Download HADDOCK parameter file for a specific project (**EASY**)
* launch_project() => Run an HADDOCK project from a parameter file (**GURU**)
* list_users() => List all HADDOCK users (output username and email) (**ADMIN**, Alex or Marc)

## Console-like environment

As a proof of concept, we designed a lightweight console-like environment (based on the [cmd2 Python module](https://github.com/python-cmd2/cmd2)) to access the different methods listed above. 

This console allows you to use the login/logout features present in HADDOCKInterface class to avoid the username/password request at each new method usage.
Within the console, all XMLRPC API methods are accessible and some of them have seen their output enhanced through the usage of arguments.

The complete list of commands (including native ones) can be obtained with `help` and each command has a description/usage output with `help command`.

## Acknowledgment

This project has been developed in the Computational Structural Biology group of Utrecht University.
Main development has been made by Mikael Trellet (mikael.trellet@gmail.com) for the python interfaces at the client side linking the work made by Marc van Dijk (m4.van.dijk@vu.nl) for the XMLRPC API on the server side.
