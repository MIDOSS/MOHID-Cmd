.. Copyright 2018-2020 the MIDOSS project contributors, The University of British Columbia,
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


.. _monte-carlo-sub-command:

**********************************
:command:`monte-carlo` Sub-command
**********************************

.. warning::
    The :command:`monte-carlo` sub-command is presently under active development,
    so frequent updates and changes in the code and thi documentation section should be expected.

The :command:`monte-carlo` sub-command prepares an MPI job to execute a collection of MIDOSS-MOHID runs,
typically for a Monte Carlo experiment.
The job uses `GLOST`_ to execute the individual runs in the context of a single MPI job.
The job is described by a YAML file that provides information for the setup and execution of the GLOST job,
and a CSV file that provides parameters of the individual MIDOSS-MOHID runs.

.. _GLOST: https://docs.computecanada.ca/wiki/GLOST


.. _GLOST-JobDescriptionYAML-File:

GLOST Job Description YAML File
===============================

Information for the setup and execution of the GLOST job is provided in a YAML file.
Here is an example:

.. code-block:: yaml

    job id: AKNS-spatial
    account: rrg-allen
    email: dlatorne@eoas.ubc.ca
    nodes: 1
    tasks per node: 3
    runs per glost job: 2
    mem per cpu: 14100M
    run walltime: 2:00:00

    paths:
      runs directory: $SCRATCH/MIDOSS/runs/monte-carlo/
      mohid config: $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config/monte-carlo/

    mohid command: $HOME/.local/bin/mohid

    vcs revisions:
      git:
        - $PROJECT/$USER/MIDOSS/Make-MIDOSS-Forcing
        - $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-grid
        - $PROJECT/$USER/MIDOSS/moad_tools
        - $PROJECT/$USER/MIDOSS/MOHID-Cmd
        - $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config
      hg:
        - $PROJECT/$USER/MIDOSS/NEMO-Cmd


.. _MOHID-RunParametersCSV-File:

MOHID Run Parameters CSV File
=============================

Parameters for the individual MIDOSS-MOHID runs are provided in a CSV file.
Here is an example:

::

    spill_date_hour, run_days, spill_lon, spill_lat, Lagrangian_template
    2017-06-15 02:00, 7, -122.86, 48.38, Lagrangian_AKNS_crude.dat
    2017-06-15 02:00, 7, -122.86, 48.38, Lagrangian_AKNS_crude.dat
