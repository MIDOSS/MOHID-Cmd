.. Copyright 2018-2019 the MIDOSS project contributors, The University of British Columbia,
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


.. _MOHID-CmdSubcommands:

*****************************
:command:`mohid` Sub-Commands
*****************************

The command :kbd:`mohid help` produces a list of the available :program:`mohid` options and sub-commands::

  usage: mohid [--version] [-v | -q] [--log-file LOG_FILE] [-h] [--debug]

  MIDOSS-MOHID Command Processor

  optional arguments:
    --version            show program's version number and exit
    -v, --verbose        Increase verbosity of output. Can be repeated.
    -q, --quiet          Suppress output except warnings and errors.
    --log-file LOG_FILE  Specify a file to log output. Disabled by default.
    -h, --help           Show help message and exit.
    --debug              Show tracebacks on errors.

  Commands:
    complete       print bash completion command (cliff)
    help           print detailed help for another command (cliff)
    prepare        Set up the MIDOSS-MOHID run described in DESC_FILE and print the path of the


For details of the arguments and options for a sub-command use
:command:`mohid help <sub-command>`.
For example:


.. code-block:: bash

    $ mohid help prepare

::

    usage: mohid prepare [-h] [-q] DESC_FILE

    Set up the MIDOSS-MOHID run described in DESC_FILE and print the path of the
    temporary run directory.

    positional arguments:
      DESC_FILE    run description YAML file

    optional arguments:
      -h, --help   show this help message and exit
      -q, --quiet  don't show the run directory path on completion


.. _mohid-prepare:

:kbd:`prepare` Sub-command
==========================

The :command:`prepare` sub-command sets up a temporary run directory from which to execute the MIDOSS-MOHID run described in the run description YAML file provided on the command-line::

  usage: mohid prepare [-h] [-q] DESC_FILE

  Set up the MIDOSS-MOHID run described in DESC_FILE and print the path of the
  temporary run directory.

  positional arguments:
    DESC_FILE    run description YAML file

  optional arguments:
    -h, --help   show this help message and exit
    -q, --quiet  don't show the run directory path on completion


See the :ref:`RunDescriptionFileStructure` section for details of the run description file.

The :command:`prepare` sub-command concludes by printing the path to the temporary run directory it created.
Example:

.. code-block:: bash

    $ mohid prepare mohid.yaml

    mohid_cmd.prepare INFO: Created temporary run directory: /scratch/dlatorne/MIDOSS/runs/example_2018-12-10T145044.750477-0800

The name of the temporary run directory created is the :kbd:`run id` string from the run description YAML file with an ISO-formatted date/time stamp appended because the directory is intended to be ephemerally used for a single run.

.. note::

    If the :command:`prepare` sub-command prints an error message,
    you can get a Python traceback containing more information about the error by re-running the command with the :kbd:`--debug` flag.
