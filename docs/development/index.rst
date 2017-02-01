.. toctree::
    development/wamp

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



.. _Crossbar: http://crossbar.io
.. _Autobahn: http://autobahn.ws
