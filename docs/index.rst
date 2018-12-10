.. Copyright 2018 the MIDOSS project contributors, The University of British Columbia,
.. and Dalhousie University.
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.


.. _MOHID-CommandProcessor:

******************************
MIDOSS-MOHID Command Processor
******************************

The MIDOSS-MOHID command processor,
:program:`mohid`,
is a command-line tool for doing various operations associated with the `MIDOSS project`_ version of the `MOHID model`_.

.. _MIDOSS project: https://midoss-docs.readthedocs.io/en/latest/
.. _MOHID model: https://www.mohid.com/

The :kbd:`MOHID-Cmd` package is a Python 3 package.
It is developed and tested under Python 3.6 and should work with that and later versions of Python.

This an extensible tool built on the OpenStack ``cliff``
(`Command Line Interface Formulation Framework`_)
package.
It uses plug-ins from the `NEMO-Cmd`_ package to provide a command processor tool that is specifically tailored to the MOHID model as it is used in the MIDOSS project.

.. _Command Line Interface Formulation Framework: https://docs.openstack.org/cliff/latest/
.. _NEMO-Cmd: https://bitbucket.org/salishsea/nemo-cmd


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   subcommands
   run_description_file/index


Indices
=======

* :ref:`genindex`
* :ref:`modindex`


License
=======

The MIDOSS-MOHID command processor code and documentation are copyright 2018 by the `MIDOSS project contributors`_,
The University of British Columbia,
and Dalhousie University.

.. _MIDOSS project contributors: https://bitbucket.org/midoss/docs/src/tip/CONTRIBUTORS.rst

They are licensed under the Apache License, Version 2.0.
https://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
