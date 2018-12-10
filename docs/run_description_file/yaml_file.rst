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


.. _RunDescriptionFile:

*********************************
MIDOSS-MOHID Run Description File
*********************************

.. _ExampleRunDescriptionYAML-File:

Example Run Description YAML File
=================================

Example (from :file:`MIDOSS-MOHID-config/examples/mohid.yaml`):

.. literalinclude:: mohid.yaml.example
   :language: yaml


.. _BasicRunConfiguration:

Basic Run Configuration
=======================

The following key-value pairs provide the basic configuration for the run:

:kbd:`run_id`
   The job identifier that appears in the temporary run directory name and the :command:`squeue` command output.


.. _PathsSection:

:kbd:`paths` Section
====================

The :kbd:`paths` section of the run description file is a collection of directory paths that :program:`mohid` uses to find files in other repos that it needs.

:kbd:`runs directory`
  The path to the directory where temporary run directories will be created by the :command:`mohid run` (or :command:`mohid prepare`) sub-command.

  This path may be relative or absolute.
  It may contain:

  * :envvar:`$SCRATCH` as an alternative spelling of the user's :file:`scratch` directory on :kbd:`cedar`
  * :envvar:`$PROJECT` as an alternative spelling of the group's :file:`project` directory on :kbd:`cedar`
  * :envvar:`$USER` as an alternative spelling of the user's userid
  * :kbd:`~` or :envvar:`$HOME` as alternative spellings of the user's home directory


See the :ref:`RunDescriptionFileStructure` section for details of the run description file.

The :command:`prepare` sub-command concludes by printing the path to the temporary run directory it created.
Example:

.. code-block:: bash

    $ mohid prepare mohid.yaml

    mohid_cmd.prepare INFO: Created temporary run directory: /tmp/mohid-runs/example_2018-12-10T145044.750477-0800

The name of the temporary run directory created is the :kbd:`run id` string from the run description YAML file with an ISO-formatted date/time stamp appended because the directory is intended to be ephemerally used for a single run.

If the :command:`prepare` sub-command prints an error message,
you can get a Python traceback containing more information about the error by re-running the command with the :kbd:`--debug` flag.
