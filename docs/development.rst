.. _development:

===========
Development
===========

In the following chapters we will guide you through the proces of writting modules for the LIEStudio ecosystem.


Application architecture
========================

LIEStudio uses the Web Application Messaging Protocol (WAMP) to enable messaging between the components of the
application. WAMP communication is handeled by the Autobahn_ familly of WAMP protocol libraries and Crossbar_
operates as WAMP router. The benefits of this approach are plentyfull:

* Autobahn currently provides WAMP libraries for 13 different languages allowing developers to easily contribute
  components to LIEStudio written in their favourite language.
* The WAMP infrastructure enabled by Autobahn and Crossbar allow messaging over TCP and Unix domain sockets as
  transport layer connecting threads, seperated processes on the same machine or processes on physically
  different machines. This flexibility allows for processes on heterogeneous infrastructures such as different
  OS versions, Virtual Machines, Docker images or different servers to be connected together. This means efficient
  scale up- and out.
* The Crossbar router in particular is a mature product that offers additional functionality on top of basic 
  routing such as: communication realms, secure transport (TLS), authorization and authentication among others.
* WAMP bundels Remote Procedure Call (RPC) and Publish & Subscribe messaging patterns in one unified protocol

WAMP messaging
==============

The WAMP based API is the only formal interface of a LIEStudio component and the application as a whole.
The code that enables the functionality of a component is to great extend shielded from the user or other 
components. To ensure that all components together form a functional whole requires the message exchange between
them to be reliable, predictable and complete.

Messages are therefor wrapped in an envelope that defines metadata on the WAMP session, the component dealing with
the request and user information on behalf of which components are contacted. 

* _realm:          WAMP realm the component is connected to
* _package_name:   Component name
* _authid:         user name
* _class_name:     name of the WAMP API class of the component
* _authrole:       user role
* _authmethod:     method used to authenticate the user
* _session:        WAMP session ID 
* _status:         status message of the task being executed as: submitted, waiting, ready, scheduled, running,
                   done, aborted, cancelled or cleared.
* _init_time:      time message was first created.
* _update_time:    time message was last updated.
* _status_message: human readable status message
* _id:             unique ID identifing the message. 

**messaging and database storage**
The above information provides a unique identifier of a message from a WAMP communication perspective, a user 
perspective and a component task perspective. As such it provides a complete foundation for storing task
information in a database. 

LIEStudio components store tasks in the database in order to store results, as a persistent store for to follow
the progress of a longer living task and to rerun a task.

WAMP Workflow Schema
====================

All communication is always wrapped in a "task" ensuring that task meta data is send along with every request.
Within the task is the request itself targeting a WAMP method. The WAMP method always accepts the task as only
argument (without optional keyword arguments). The task contains all data required by the method. This way
of working allows the WAMP method to safely extend it's capabilities without breaking the API. Intelligence is
with the WAMP service.

The data required by the WAMP method is always and "input" and a "config" object. Input can be "inline" not having
any dependencies or link to another WAMP method as provider. In the latter case the input itself forms the new
task call to the WAMP method serving as input provider.
A config object holds additional metadata (optionally) required by the WAMP method to perform the action. It is
best practice for the component hosting the WAMP service to define defaults for the configuration. When using the
config API, the default configuration can be overruled by the custom configuration provided. 

The combination of task metadata, input and config data in one object allows the targeted WAMP method to store
an atomic task object in the database using the unique task ID. As the same task ID is also returned with the 
methods (intermediate) results, the sender knows where to find the data or how to ask for it.
This also allows a workflow to be repeated in the same manner as all data and settings are known at every stage
of the workflow.

A task datamodel construct for a PLANTS docking run could look like this:

.. code-block:: python

    {
    _taskMeta: {
        _realm:         
        _package_name:  
        _authid:        
        _class_name:    
        _authrole:      
        _authmethod:    
        _session:       
        _status:        
        _init_time:     
        _update_time:   
        _status_message:
        _id:            
    },
    '_dataType': 'wampMethod',
    '_wampUrl': 'liestudio.docking.run',
    '_inputDict': {
        'ligandFile': {
        '_dataType': 'wampMethod',
        '_wampUrl': 'liestudio.structure.get',
        '_configDict': {
            'structure_id': '100203',
            'format': 'mol2'
        },
        },
        proteinFile: {
        '_dataType': 'inlineSource',
        '_data: '<structure inline pdb>',
        }
    },
    _outputDict: {
        '<results>'
    },
    _configDict: {
        'method', 'plants',
        'workdir': '/home/workdir',
        'bindingsite_center': [0,0,0]
    }
    }

**Message type**
LIEStudio tasks communicate data in a number of predefined types indicated by the '_dataType' tage:

* wampMethod: the data to be send or retrieved is handeled by a different WAMP method and thus can
              be regarded as a new task. A data construct if type wampMethod is required to have the
              _wampUrl tag with the fully qualified WAMP URL of the method to be called and either a
              _inputDict or _configDict depending on the method specifications. Other tags are optional.
* inlineSource: the data is send inline using the _data tag. 
* fileSource: the data is located in a file at the '_url' location with optional tags '_fileType'

**_inputDict**
WAMP methods may accept an arbitrary number of input values. These can be regarded as the arguments 
of a Python function. Keyword arguments are stored in the _configDict.
Each input is of a certain data type as described above.

**_outputDict**
Equal to the _inputDict in capabilities.

**_configDict**
Keyword values to the method.


.. _Crossbar: http://crossbar.io
.. _Autobahn: http://autobahn.ws