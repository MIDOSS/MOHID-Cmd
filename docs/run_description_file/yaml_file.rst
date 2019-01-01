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

:kbd:`mohid repo`
  The path to the `MIDOSS-MOHID`_ repository clone where the :file:`MohidWater.exe` executable for the run is to be found.

  .. _MIDOSS-MOHID: https://bitbucket.org/midoss/midoss-mohid/

  This path may be either absolute or relative.
  It may contain:

  * :envvar:`$SCRATCH` as an alternative spelling of the user's :file:`scratch` directory on :kbd:`cedar`
  * :envvar:`$PROJECT` as an alternative spelling of the group's :file:`project` directory on :kbd:`cedar`
  * :envvar:`$USER` as an alternative spelling of the user's userid
  * :kbd:`~` or :envvar:`$HOME` as alternative spellings of the user's home directory

  Absolute paths with environment variables are strongly recommended for portability and re-usability.

:kbd:`runs directory`
  The path to the directory where temporary run directories will be created by the :command:`mohid run` (or :command:`mohid prepare`) sub-command.

  This path may be relative or absolute.
  It may contain:

  * :envvar:`$SCRATCH` as an alternative spelling of the user's :file:`scratch` directory on :kbd:`cedar`
  * :envvar:`$PROJECT` as an alternative spelling of the group's :file:`project` directory on :kbd:`cedar`
  * :envvar:`$USER` as an alternative spelling of the user's userid
  * :kbd:`~` or :envvar:`$HOME` as alternative spellings of the user's home directory

  Absolute paths with environment variables are strongly recommended for portability and re-usability.


.. _ForcingSection:

:kbd:`forcing` Section
======================

The :kbd:`forcing` section of the run description file contains key-value pairs that provide the names of files that are to be symlinked in the temporary run directory for MOHID to read forcing data from.

An example :kbd:`forcing` section:

.. code-block:: yaml

    forcing:
      winds.hdf5: $PROJECT/MIDOSS/forcing/HRDPS/atmosphere_20150408_20150414.hdf5
      currents.hdf5: $PROJECT/MIDOSS/forcing/SalishSeaCast/hydrodynamics_20150408_20150414.hdf5
      water_levels.hdf5: $PROJECT/MIDOSS/forcing/SalishSeaCast/hydrodynamics_20150408_20150414.hdf5

The keys
(:kbd:`winds.hdf5`,
:kbd:`currents.hdf5`,
and :kbd:`water_levels.hdf5` above)
are the names of the symlinks that will be created in the temporary run directory.
Those names are expected to appear in the appropriate places in the :file:`.dat` files.
The values associated with the keys are the targets of the symlinks that will be created in the temporary run directory.

The paths may be relative or absolute.
They may contain:

* :envvar:`$SCRATCH` as an alternative spelling of the user's :file:`scratch` directory on :kbd:`cedar`
* :envvar:`$PROJECT` as an alternative spelling of the group's :file:`project` directory on :kbd:`cedar`
* :envvar:`$USER` as an alternative spelling of the user's userid
* :kbd:`~` or :envvar:`$HOME` as alternative spellings of the user's home directory

Absolute paths with environment variables are strongly recommended for portability and re-usability.


.. _BathymetryPath:

:kbd:`bathymetry` Path
======================

The path and file name of the bathymetry file to use for the run is given by the value associated with the :kbd:`bathymetry` key.
The bathymetry path is inserted into the :file:`nomfich.dat` file that is created in the temporary run directory as the value associated with the :kbd:`IN_BATIM` key.

An example :kbd:`bathymetry` line:

.. code-block:: yaml

    bathymetry: $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config/SalishSeaCast/SalishSeaCast_bathymetry.dat

The path may be relative or absolute.
It may contain:

* :envvar:`$SCRATCH` as an alternative spelling of the user's :file:`scratch` directory on :kbd:`cedar`
* :envvar:`$PROJECT` as an alternative spelling of the group's :file:`project` directory on :kbd:`cedar`
* :envvar:`$USER` as an alternative spelling of the user's userid
* :kbd:`~` or :envvar:`$HOME` as alternative spellings of the user's home directory

An absolute path with environment variables is strongly recommended for portability and re-usability.


.. _RunDataFilesSection:

:kbd:`run data files` Section
=============================

The :kbd:`run data files` section of the run description file contains key-value pairs that provide the keywords and paths to run data files that will be used to build the :file:`nomfich.dat` file that MOHID requires.

An example :kbd:`run data files` section:

.. code-block:: yaml

    run data files:
      IN_MODEL: $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config/MarathassaConstTS/Model.dat
      PARTIC_DATA: $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config/MarathassaConstTS/Lagrangian.dat
      DOMAIN: $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config/SalishSeaCast/Geometry.dat
      SURF_DAT: $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config/SalishSeaCast/Atmosphere.dat
      DOMAIN: $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config/SalishSeaCast/Geometry.dat
      IN_DAD3D: $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config/SalishSeaCast/Hydrodynamic.dat
      BOT_DAT: $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config/SalishSeaCast/InterfaceSedimentWater.dat
      AIRW_DAT: $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config/SalishSeaCast/InterfaceWaterAir.dat
      IN_TIDES: $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config/SalishSeaCast/Tide.dat
      IN_TURB: $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config/SalishSeaCast/Turbulence.dat
      DISPQUAL: $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config/SalishSeaCast/WaterProperties.dat
      WAVES_DAT: $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config/SalishSeaCast/Waves.dat

The path may be relative or absolute.
It may contain:

* :envvar:`$SCRATCH` as an alternative spelling of the user's :file:`scratch` directory on :kbd:`cedar`
* :envvar:`$PROJECT` as an alternative spelling of the group's :file:`project` directory on :kbd:`cedar`
* :envvar:`$USER` as an alternative spelling of the user's userid
* :kbd:`~` or :envvar:`$HOME` as alternative spellings of the user's home directory

An absolute path with environment variables is strongly recommended for portability and re-usability.

Necessary HDF5 results file keywords and paths are automatically added to :file:`nomfich.dat`.
The HDF5 results files are stored in the :file:`res/` sub-directory of the temporary run directory
(the path that MOHID requires).
Their file names are the :file:`.dat` file stem with the :kbd:`run_id` appended,
and the extension :file:`.hdf`.
For example, if the value associated with the :kbd:`run_id` key in the run description YAML file is :kbd:`MarathassaConstTS`,
the

.. code-block:: yaml

    PARTIC_DATA: $PROJECT/$USER/MIDOSS/MIDOSS-MOHID-config/MarathassaConstTS/Lagrangian.dat

line in the :kbd:`run data files` section causes the following 2 lines to be added to the :file:`nomfich.dat` file:

.. code-block:: yaml

    PARTIC_DATA : /project/def-allen/dlatorne//MIDOSS/MIDOSS-MOHID-config/MarathassaConstTS/Lagrangian.dat
    PARTIC_HDF  : /project/def-allen/dlatorne//MIDOSS/MIDOSS-MOHID-config/MarathassaConstTS/Lagrangian_MarathassaConstTS.hdf
