******************************
MIDOSS-MOHID Command Processor
******************************

.. image:: https://img.shields.io/badge/license-Apache%202-cb2533.svg
    :target: https://www.apache.org/licenses/LICENSE-2.0
    :alt: Licensed under the Apache License, Version 2.0
.. image:: https://img.shields.io/badge/python-3.7-blue.svg
    :target: https://docs.python.org/3.7/
    :alt: Python Version
.. image:: https://img.shields.io/badge/version%20control-hg-blue.svg
    :target: https://bitbucket.org/midoss/mohid-cmd/
    :alt: Mercurial on Bitbucket
.. image:: https://img.shields.io/bitbucket/issues/43ravens/nemo_nowcast.svg
    :target: https://bitbucket.org/midoss/mohid-cmd/issues?status=new&status=open
    :alt: Issue Tracker

The MIDOSS-MOHID command processor, ``mohid``, is a command line tool for doing various operations associated with the `MIDOSS project`_ version of the `MOHID model`_.

.. _MIDOSS project: https://midoss-docs.readthedocs.io/en/latest/
.. _MOHID model: https://www.mohid.com/

Use ``mohid --help`` to get a list of the sub-commands available for doing things with and related to MIDOSS-MOHID.
Use ``mohid help <sub-command>`` to get a synopsis of what a sub-command does,
what its required arguments are,
and what options are available to control it.

Documentation for the package is in the ``docs/`` directory and is rendered at http://mohid-cmd.readthedocs.org/en/latest/.

.. image:: https://readthedocs.org/projects/mohid-cmd/badge/?version=latest
    :target: https://mohid-cmd.readthedocs.io/en/latest/
    :alt: Documentation Status

This an extensible tool built on the OpenStack ``cliff``
(`Command Line Interface Formulation Framework`_)
package.
It uses plug-ins from the `NEMO-Cmd`_ package to provide a command processor tool that is specifically tailored to the MOHID model as it is used in the MIDOSS project.

.. _Command Line Interface Formulation Framework: https://docs.openstack.org/cliff/latest/
.. _NEMO-Cmd: https://bitbucket.org/salishsea/nemo-cmd


License
=======

.. image:: https://img.shields.io/badge/license-Apache%202-cb2533.svg
    :target: https://www.apache.org/licenses/LICENSE-2.0
    :alt: Licensed under the Apache License, Version 2.0

The MIDOSS-MOHID command processor code and documentation are copyright 2018-2020 by the MIDOSS project contributors,
The University of British Columbia,
and Dalhousie University.

They are licensed under the Apache License, Version 2.0.
https://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
