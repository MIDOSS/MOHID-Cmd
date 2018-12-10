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


.. _RunDescriptionFileStructure:

******************************
Run Description File Structure
******************************

:program:`mohid` run description files are written in YAML_.
They contain key-value pairs that define the names and locations of files and directories that :program:`mohid` uses to manage MIDOSS-MOHID runs and their results.

.. _YAML: http://pyyaml.org/wiki/PyYAMLDocumentation

Run description files are typically stored in a sub-directory of your clone of the :ref:`MIDOSS-MOHID-config-repo`.

.. toctree::
   :maxdepth: 3

   yaml_file
