.. Copyright 2018-2021 the MIDOSS project contributors, The University of British Columbia,
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
    so frequent updates and changes in the code and this documentation section should be expected.

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
    mem per cpu: 14100M
    run walltime: 2:00:00

    paths:
      forcing directory: $SCRATCH/MIDOSS/forcing/
      runs directory: $SCRATCH/MIDOSS/runs/monte-carlo/
      mohid config: $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config/monte-carlo/

    make-hdf5 command: $HOME/.local/bin/make-hdf5
    mohid command: $HOME/.local/bin/mohid

    vcs revisions:
      git:
        - $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-CODE
        - $PROJECT/$USER/MIDOSS/Make-MIDOSS-Forcing
        - $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-grid
        - $PROJECT/$USER/MIDOSS/SalishSeaCast-grid
        - $PROJECT/$USER/MIDOSS/moad_tools
        - $PROJECT/$USER/MIDOSS/NEMO-Cmd
        - $PROJECT/$USER/MIDOSS/MOHID-Cmd
        - $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config


.. _MOHID-RunParametersCSV-File:

MOHID Run Parameters CSV File
=============================

Parameters for the individual MIDOSS-MOHID runs are provided in a CSV file.
Here is an example:

::

    spill_date_hour, run_days, spill_lon, spill_lat, Lagrangian_template
    2017-06-15 02:00, 7, -122.86, 48.38, Lagrangian_AKNS_crude.dat
    2017-06-15 02:00, 7, -122.86, 48.38, Lagrangian_AKNS_crude.dat


.. _MonteCarloHowItWorks:

How It Works
============

Running the :command:`mohid monte-carlo` command with a YAML file like the one above,
and a CSV file containg parameter lines for 5 runs results in the creation of a directory tree for a collection of 5 MOHID runs that will be executed as a single MPI job under `GLOST`_,
and submission of that job to the scheduler via :command:`sbatch`.

The directory tree will be created in the directory given by the :kbd:`runs directory` item in the :kbd:`paths` stanza of the YAML file;
:file:`$SCRATCH/MIDOSS/runs/monte-carlo/` in our example above.
The name of the directory tree will be the :kbd:`job id` given in the YAML file with a date/time stamp appended to it.
The date/time is that at which the :command:`mohid monte-carlo` command is run.
So, for the YAML file above,
the directory tree created would be :file:`$SCRATCH/MIDOSS/runs/monte-carlo/AKNS-spatial_2020-04-30T173543`
(with a different date/time suffix, of course).

Initially that directory tree would look like::

  ├── forcing-yaml/
  │   ├── AKNS-spatial-make-hdf5-0.yaml
  │   ├── AKNS-spatial-make-hdf5-1.yaml
  │   ├── AKNS-spatial-make-hdf5-2.yaml
  │   ├── AKNS-spatial-make-hdf5-3.yaml
  │   ├── AKNS-spatial-make-hdf5-4.yaml
  │   └── README.rst
  ├── glost-job.sh
  ├── glost-tasks/
  │   ├── AKNS-spatial-0.sh
  │   ├── AKNS-spatial-1.sh
  │   ├── AKNS-spatial-2.sh
  │   ├── AKNS-spatial-3.sh
  │   ├── AKNS-spatial-4.sh
  │   └── README.rst
  ├── glost-tasks.txt
  ├── AKNS-spatial.csv
  ├── AKNS-spatial.yaml
  ├── MIDOSS-MOHID-CODE_rev.txt
  ├── MIDOSS-MOHID-config_rev.txt
  ├── MIDOSS-MOHID-grid_rev.txt
  ├── moad_tools_rev.txt
  ├── MOHID-Cmd_rev.txt
  ├── mohid-yaml/
  │   ├── AKNS-spatial-0.yaml
  │   ├── AKNS-spatial-1.yaml
  │   ├── AKNS-spatial-2.yaml
  │   ├── AKNS-spatial-3.yaml
  │   ├── AKNS-spatial-4.yaml
  │   ├── Lagrangian_AKNS_crude-0.dat
  │   ├── Lagrangian_AKNS_crude-1.dat
  │   ├── Lagrangian_AKNS_crude-2.dat
  │   ├── Lagrangian_AKNS_crude-3.dat
  │   ├── Lagrangian_AKNS_crude-4.dat
  │   ├── Model-0.dat
  │   ├── Model-1.dat
  │   ├── Model-2.dat
  │   ├── Model-3.dat
  │   ├── Model-4.dat
  │   └── README.rst
  ├── NEMO-Cmd_rev.txt
  └── results/
      ├── AKNS-spatial-0/
      ├── AKNS-spatial-1/
      ├── AKNS-spatial-2/
      ├── AKNS-spatial-3/
      ├── AKNS-spatial-4/
      └── README.rst

* The :file:`forcing-yaml/` directory contains YAML config files to drive :command:`make-hdf5` for each of the runs.
  They are generated from the https://github.com/MIDOSS/MIDOSS-MOHID-config/blob/main/monte-carlo/templates/make-hdf5.yaml template.

* The :file:`glost-job.sh` file is the shell script that is submitted via :command:`sbatch` to run run Monte Carlo GLOST job.

* The :file:`glost-tasks/` directory contains shell scripts for each of the individual MOHID runs that GLOST farms.
  They are generated from the https://github.com/MIDOSS/MIDOSS-MOHID-config/blob/main/monte-carlo/templates/glost-task.sh template.

* The :file:`glost-tasks.txt` file is the collection of bash execution lines for the scripts in the :file:`glost-tasks/` directory.
  This is the file that GLOST uses to launch each of the MOHID runs.

* The :file:`AKNS-spatial.csv` file is the CSV file from the command-line.

* The :file:`AKNS-spatial.yaml` file is the YAMl file from the command-line.

* The :file:`*_rev.txt` files are VCS recording files.

* The :file:`mohid-yaml/` directory contains YAML run description files for each of the MOHID runs.
  They are generated from the https://github.com/MIDOSS/MIDOSS-MOHID-config/blob/main/monte-carlo/templates/mohid-run.yaml template.

* The :file:`results/` directory will be empty at this point except for it's :file:`README.rst` file.

When the scheduler starts execution of the job,
two more files will appear:

* :file:`glost-job.stderr`

* :file:`glost-job.stdout`

The first step of execution in each :file:`glost-task.sh` script is to run :command:`make-hdf5` to generate the HDF5 forcing files for the MOHID runs.
That typically takes 20 to 30 minutes of run time.
Nothing happens in the GLOST job directory tree during that step,
but the HDF5 forcing files gradually appear in directories within the directory given by the :kbd:`forcing directory` item in the :kbd:`paths` stanza of the YAML file.
For the example above,
the HDF5 forcing file directories would have names like :file:`$SCRATCH/MIDOSS/forcing/AKNS-spatial-0/ddmmmyy-ddmmmyy/`,
where

* :kbd:`AKNS-spatial` is the :kbd:`job id` from the YAML file
* The digit(s) appended to it after the :kbd:`-` are the 0-based row numbers from the CSV file
* :kbd:`ddmmmyy-ddmmmyy` are the start and end dates of the runs from the CSV file rows

The HDF5 files are generated in directories that are specific to the MOHID runs in the Monte Carlo GLOST job.
They are only used for that run,
and they are deleted at the end of the run.
That is done so as to avoid the possibility of multiple jobs with the same start date and duration that happen to  execute concurrently all trying to write forcing files to the same directory.

.. note::
    Please ensure that you have created the directory in which your HDF5 forcing file directories will be created before running :command:`mohid monte-carlo` for the first time;
    e.g. :kbd:`mkdir -p $SCRATCH/MIDOSS/forcing`.

After :command:`make-hdf5` finishes the :file:`glost-job.stdout` file will contain its output for each of the forcing files directories that were created.

The second step of execution in each :file:`glost-task.sh` script is to run :command:`mohid run --no-submit` to add temporary run directories to the tree.
They are named like :file:`AKNS-spatial-0/`,
composed of the :kbd:`job id`,
and the run number that is the 0-based row number from the CSV file.

The third step of execution in each :file:`glost-task.sh` script is to bash execute the :file:`MOHID.sh` script for the run.
The run results are gathered in the directories under :file:`results/`;
e.g. :file:`results/AKNS-spatial-0`.

The final step of execution in each :file:`glost-task.sh` script is to remove the HDF5 forcing files directory that was created for the MOHID run in the first step.
