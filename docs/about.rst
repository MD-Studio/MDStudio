.. _about:

=====
About
=====

LIEStudio is an interactive application to explore molecular interactions between small ligands and proteins 
using powerful molecular simulation, data analysis and visualization techniques. The LIEStudio application 
has been constructed with a number of "design goals" in mind that make it:

- **Flexible**:

  LIEStudio uses an event driven programming design where individual tasks such as docking or simulations are
  handeled by dedicated modules that communicate with one another using the WAMP_ messaging protocol (Web Application
  Messaging Protocol) implemented using the Crossbar_ WAMP router. 
  
  The functionality of these modules is available at the script level and via a graphical user interface (GUI)
  implemented as a web browser application. Performing complicated tasks is now as easy as chaining together the
  methods that the individual modules expose in a controled manner.
  
  The LIEStudio API enables easy extention of the applications functionality by addition of new (custom) modules
  that extend the functionality. The individual modules can be written in any of the 12 languages_ for wich a WAMP
  API is available allowing you to build modules in your language of choice. Most of the default modules shipped 
  with the application are written in Python_

.. _Python: http://www.python.org
.. _WAMP: http://wamp-proto.org
.. _Crossbar: http://crossbar.io
.. _languages: http://crossbar.io/about/Supported-Languages/