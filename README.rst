********
EazyCtrl
********

Python module and command line tool to monitor and control the air exchangers of
Helios (KWL EasyControls) via their Modbus/TCP interface. It allows for an easy
command line handling of the devices and for a smooth integration of those into
smart home systems (e.g. Home Assistant).

**Important note**: The module and the command line tool were created based on
the publicly accessible documentation for the EasyControls Modbus/TCP interface
and for the Modbus/TCP protocol. They were only tested with a Helios KWL EC 300
W air exchanger. **Use them on your own risk**.


Installing
==========

EazyCtrl should work with any recent Python 3 interpreters. (It has been tested
with Python 3.6).

Use Pythons command line installer ``pip`` to install it::

  pip install eazyctrl

This installs both, the single file command line tool ``eazyctrl`` and the
single file Python module ``eazyctrl.py``. Latter you can import if you want to
access the functionality from within your Python scripts.


Using as command line tool
==========================

All functionality can be accessed through the command line script
``eazyctrl``. In order to get information about the possible command line
options, issue ::

  eazyctrl -h

If you want help about a given subcommand, add the subcommand name before the
``-h`` option, e.g. ::

  eazyctrl set -h

will list the available options for the ``set`` subcommand.


Obtaining the feature list
--------------------------

In order to list the features which you can access through ``eazyctrl``, use the
``list`` subcommand::

  eazyctrl list

This would return a table containing the feature names, their access flag
(read-only or read-write) and the corresponding variable, e.g.::

  Feature name                   Access Variable
  ----------------------------------------------
  fan_stage                      rw     v00102  
  temp_outside_air               r      v00104  
  temp_supply_air                r      v00105  
  temp_outgoing_air              r      v00106  
  temp_extract_air               r      v00107


Note, that not all variables have been mapped to features yet. Those, not in the
table can be queried and set by the low-level variable access methods (see
below). But whenever a named feature is available for a given variable, it is
recommended to use the more convenient and more robust access via the feature.


Getting the value of a feature
------------------------------

Use the ``get`` subcommand to query the value of a given feature.

For example, to query the temperature of the outside air, issue::

  eazyctrl get helios-kwl.fritz.box temp_outside_air

The first argument is the host name of the remote device (or its IP-address),
followed by the feature name. The result is printed on the console, like::

  23.3


Setting the value of a feature
------------------------------

Use the ``set`` subcommand to set the value of a given feature.

For example, in order to set the fan stage to level 2, issue::

  eazyctrl set helios-kwl.fritz.box fan_stage 2

If the script returns without error message, the communication with the device
was successful.


Getting the value of a variable
-------------------------------

The command line tool allows to query a variable directly by using its name.
This direct variable accesss should only be used, if the given variable has not
been mapped to a feature yet.

Additionally to the name of the variable, you also have to provide the maximal
length of the expected answer (which can be looked up in the EasyControls
manual).

For example, to query the fan stage by reading the variable ``v00102``, issue ::

  eazyctrl getvar helios-kwl.fritz.box v00102 1


Setting the value of a variable
-------------------------------

The command line tool allows to set a variable directly by using its name.  This
direct variable accesss should only be used, if the given variable has not been
mapped to a feature yet.

Note, that the value you provide for the variable must be exactly in the right
format since it is passed unaltered to the remote device. Consult the
EasyControls manual about the expected format for each variable.

For example, to set the fan stage directly via the ``v00102`` variable, issue ::

  eazyctrl setvar helios-kwl.fritz.box v00102 1


Using EazyCtrl as a Python module
=================================

The functionality of EazyCtrl can be accessed using the ``eazyctrl`` Python
module. The module can be imported in the usual way ::

  import eazyctrl

The high level class `EazyController` provides an access similar to the command
line tool.


Obtaining the feature list
--------------------------

The static method ``get_feature_list()`` returns the available
features. It returns a list of tuples, each one containing the name of the
feature and a dictionary with various parameters of that feature.

For example the snippet ::

  host = 'helios-kwl.fritz.box'   # replace with the IP-address of your device
  ftrlist = eazyctrl.EazyController.get_feature_list()
  print(ftrlist)

results in ::

  [('fan_stage', {'rw': True, 'varname': 'v00102'}),
   ('temp_outside_air', {'rw': False, 'varname': 'v00104'}),
   ('temp_supply_air', {'rw': False, 'varname': 'v00105'}),
   ('temp_outgoing_air', {'rw': False, 'varname': 'v00106'}),
   ('temp_extract_air', {'rw': False, 'varname': 'v00107'})]


Getting the value of a feature
------------------------------

The method ``get_feature()`` returns the value of a given feature. The value is
converted to an appropriate Python type (e.g. integer, float, etc.).

The following example queries the value of the outside air temperature sensor ::

  host = 'helios-kwl.fritz.box'   # replace with the IP-address of your device
  ctrl = eazyctrl.EazyController(host)
  temp_out = ctrl.get_feature('temp_outside_air')
  print(temp_out, type(temp_out))

This results in ::

  24.4 <class 'float'>


Setting the value of a feature
------------------------------

You can use the ``set_feature()`` method to set a value for a given feature. You
should provide the value as a Python type (e.g. integer, float, etc.) and it
will be automatically converted to the right text representation before being
passed to the device.

For example, you can set the fan stage to level 3 by the following snippet::

  host = 'helios-kwl.fritz.box'   # replace with the IP-address of your device
  ctrl = eazyctrl.EazyController(host)

  # Setting the fan stage
  success = ctrl.set_feature('fan_stage', 3)
  print(success)

  # Querying the fan stage to check, whether it has the desired value now
  fan_stage = ctrl.get_feature('fan_stage')
  print(fan_stage)

The ``set_feature()`` method returns ``True`` or ``False`` indicating whether
the communication with the device was successful or not. So, for the snippet
above, you should get the output ::

  True
  3

and of course, the fan should have been switched to stage 3.


Getting the value of a variable
-------------------------------

Similar to the command line tool, the `EazyController` object allows direct
variable access as well. This low-level function returns the response of the
server unaltered as a string, unless you specify a conversion function. Beyond
the variable name, you also have to pass the length of the expected answer (to
be found in the EasyConfigs manual).

Let's query the outside air temperature via the v00104 variable and convert it
to a float value ::

  host = 'helios-kwl.fritz.box'   # replace with the IP-address of your device
  ctrl = eazyctrl.EazyController(host)
  temp_out = ctrl.get_variable('v00104', 7, conversion=float)


Setting the value of a variable
-------------------------------

Via the ``set_variable()`` method you can set the value of a given variable.

The example below, sets the fan stage using the variable ``v00102``. It also
demonstrates, that you can use a formatting string instead of a conversion
function for the ``conversion`` argument::

  host = 'helios-kwl.fritz.box'   # replace with the IP-address of your device
  ctrl = eazyctrl.EazyController(host)

  # Setting the variable
  ctrl.set_variable('v00102', 3, conversion="{:d}")

  # Check, whether the variable contains the right value
  fan_stage = ctrl.get_variable('v00102', 1, conversion=int)

  print("Expected: {:d}, obtained {:d}".format(3, fan_stage))

If everything went well, you should obtain ::

  Expected: 3, obtained 3


Notes on concurrent access conflicts
====================================

Due to its design, the EasyControls protocol can not deal well with concurrent
accesses of multiple clients. Especially, reading out a variable/feature is very
error-prone as it needs two communications. The first communication tells the
server, which variable should be queried, while the actual value is returned
during a second communication. If between the first and second communication a
second client starts a query for a different variable, the first client may get
back the value for the wrong variable (namely the one the second client asked
for).

When EazyCtrl detects, that the wrong variable was returned, it will repeat the
given query again after a short random time delay (maximally 3 times). While
this strategy should be enough to resolve concurrent access conflicts in typical
use cases, it may fail if too many clients / threads are accessing the same
device concurrently at the same time.

In order to prevent issues due to concurrent acces, make sure that only a single
client or thread accesses the device at a given time. If your home automation
system tends to use concurrent threads to query various values simultaneously
(e.g. air temperatures), you may need to pipe the queries through a single proxy
object with locking features to ensure serial access.


License
=======

EazyCtrl is distributed under the terms of the *2-clause BSD License*.
