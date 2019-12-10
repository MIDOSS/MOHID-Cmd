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
    gather         Gather results files from a MIDOSS-MOHID run.
    help           print detailed help for another command (cliff)
    monte-carlo    Prepare for and execute a collection of Monte Carlo runs of the MIDOSS-MOHID model.
    prepare        Set up the MIDOSS-MOHID run described in DESC_FILE and print the path of the temporary run directory.
    run            Prepare, execute, and gather results from a MIDOSS-MOHID model run.

For details of the arguments and options for a sub-command use
:command:`mohid help <sub-command>`.
For example:

.. code-block:: bash

    $ mohid help run

::

    usage: mohid run [-h] [--no-submit] [-q] DESC_FILE RESULTS_DIR

    Prepare, execute, and gather the results from a MIDOSS-MOHID run described in
    DESC_FILE. The results files from the run are gathered in RESULTS_DIR. If
    RESULTS_DIR does not exist it will be created.

    positional arguments:
      DESC_FILE    run description YAML file
      RESULTS_DIR  directory to store results into

    optional arguments:
      -h, --help   show this help message and exit
      --no-submit  Prepare the temporary run directory, and the bash script to
                   execute the MOHID run, but don't submit the run to the queue.
                   This is useful during development runs when you want to hack on
                   the bash script and/or use the same temporary run directory
                   more than once.
      -q, --quiet  don't show the run directory path or job submission message

You can check what version of :program:`mohid` you have installed with:

.. code-block:: bash

    mohid --version


.. _salishsea-run:

:kbd:`run` Sub-command
======================

The :command:`run` sub-command prepares,
executes,
and gathers the results from the MIDOSS-MOHID run described in the specified run description YAML file.
The results are gathered in the specified results directory.

::

    usage: mohid run [-h] [--no-submit] [-q] DESC_FILE RESULTS_DIR

    Prepare, execute, and gather the results from a MIDOSS-MOHID run described in
    DESC_FILE. The results files from the run are gathered in RESULTS_DIR. If
    RESULTS_DIR does not exist it will be created.

    positional arguments:
      DESC_FILE    run description YAML file
      RESULTS_DIR  directory to store results into

    optional arguments:
      -h, --help   show this help message and exit
      --no-submit  Prepare the temporary run directory, and the bash script to
                   execute the MOHID run, but don't submit the run to the queue.
                   This is useful during development runs when you want to hack on
                   the bash script and/or use the same temporary run directory
                   more than once.
      -q, --quiet  don't show the run directory path or job submission message

The path to the run directory,
and the response from the job queue manager
(typically a job number)
are printed upon completion of the command.

The :command:`run` sub-command does the following:

#. Execute the :ref:`mohid-prepare` to set up a temporary run directory from which to execute the MIDOSS-MOHID run.

#. Create a :file:`MOHID.sh` job script in the temporary run directory.
   The job script:

   * runs MOHID

   * executes the :command:`hdf5-to-netcdf4` command to transform the MOHID :file:`Lagrangian.hdf5` output file into a netCDF4 file

   * executes the :ref:`mohid-gather` to collect the run description and results files into the results directory

.. note::
    If the :command:`run` sub-command prints an error message,
    you can get a Python traceback containing more information about the error by re-running the command with the :kbd:`--debug` flag.


.. _mohid-monte-carlo:

:kbd:`monte-carlo` Sub-command
==============================

.. warning::
    The :command:`monte-carlo` sub-command is presently under active development,
    so frequent updates and changes in the code and associated documentation in the ref:`monte-carlo-sub-command` section should be expected.

The :command:`monte-carlo` sub-command prepares an MPI job to execute a collection of MIDOSS-MOHID runs,
typically for a Monte Carlo experiment.
The job uses `GLOST`_ to execute the individual runs in the context of a single MPI job.
The job is described by a YAML file that provides information for the setup and execution of the GLOST job,
and a CSV file that provides parameters of the individual MIDOSS-MOHID runs.

.. _GLOST: https://docs.computecanada.ca/wiki/GLOST

Please see the :ref:`monte-carlo-sub-command` section for details of the YAML and CSV files,
how :command:`monte-carlo` works,
and the directory structure that it produces.

::

    usage: mohid monte-carlo [-h] [--no-submit] DESC_FILE CSV_FILE

    Prepare for and execute a collection of Monte Carlo runs of the MIDOSS-MOHID
    model as a glost job. The glost job is described in DESC_FILE. The parameters
    of the MIDOSS-MOHID runs are defined in CSV_FILE. The results directories from
    the runs are gathered in RESULTS_DIR. If RESULTS_DIR does ont exist, it will
    be created.

    positional arguments:
      DESC_FILE    glost job description YAML file
      CSV_FILE     MIDOSS-MOHID run parameters CSV file

    optional arguments:
      -h, --help   show this help message and exit
      --no-submit  Prepare the directories of forcing YAML files,
                   MIDOSS-MOHID run description YAML files,
                   top level results directory,
                   and the bash script to execute the glost job,
                   but don't submit the glost job to the queue.
                   This is useful during development runs when you want to hack on
                   the bash script and/or use the same setup directories
                   more than once.

.. note::
    If the :command:`monte-carlo` sub-command prints an error message,
    you can get a Python traceback containing more information about the error by re-running the command with the :kbd:`--debug` flag.


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


.. _mohid-gather:

:kbd:`gather` Sub-command
=========================

The :command:`gather` sub-command moves results from a MIDOSS-MOHID run into a results directory::

  usage: mohid gather [-h] RESULTS_DIR

  Gather the results files from the MIDOSS-MOHID run in the present working
  directory into files in RESULTS_DIR. The run description YAML file,
  `nomfich.dat` file, and other files that define the run are also gathered into
  RESULTS_DIR. If RESULTS_DIR does not exist it will be created.

  positional arguments:
    RESULTS_DIR  directory to store results into

  optional arguments:
    -h, --help   show this help message and exit

.. note::
    If the :command:`gather` sub-command prints an error message,
    you can get a Python traceback containing more information about the error by re-running the command with the :kbd:`--debug` flag.
