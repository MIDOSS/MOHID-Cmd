.. Copyright 2018-2019, the MIDOSS project contributors, The University of British Columbia,
.. and Dalhousie University.
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    https://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.


.. _MOHID-CmdPackagedDevelopment:

************************************
:kbd:`mohid_cmd` Package Development
************************************


.. image:: https://img.shields.io/badge/license-Apache%202-cb2533.svg
    :target: https://www.apache.org/licenses/LICENSE-2.0
    :alt: Licensed under the Apache License, Version 2.0
.. image:: https://img.shields.io/badge/python-3.6+-blue.svg
    :target: https://docs.python.org/3.7/
    :alt: Python Version
.. image:: https://img.shields.io/badge/version%20control-hg-blue.svg
    :target: https://bitbucket.org/midoss/mohid-cmd/
    :alt: Mercurial on Bitbucket
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://black.readthedocs.io/en/stable/
    :alt: The uncompromising Python code formatter
.. image:: https://readthedocs.org/projects/mohid-cmd/badge/?version=latest
    :target: https://mohid-cmd.readthedocs.io/en/latest/
    :alt: Documentation Status
.. image:: https://img.shields.io/bitbucket/issues/midoss/mohid-cmd.svg
    :target: https://bitbucket.org/midoss/mohid-cmd/issues?status=new&status=open
    :alt: Issue Tracker

The MIDOSSMOHID command processor package, ``MOHID-Cmd``, provides the ``mohid``
command-line tool for doing various operations associated with the `MIDOSS project`_ version of the `MOHID model`_.

.. _MIDOSS project: https://midoss-docs.readthedocs.io/en/latest/
.. _MOHID model: http://www.mohid.com/

.. _MOHID-CmdPythonVersions:

Python Versions
===============

.. image:: https://img.shields.io/badge/python-3.6+-blue.svg
    :target: https://docs.python.org/3.7/
    :alt: Python Version

The :kbd:`mohid_cmd` package is developed and tested using `Python`_ 3.7 or later.
The package uses some Python language features that are not available in versions prior to 3.6,
in particular:

* `formatted string literals`_
  (aka *f-strings*)
* the `file system path protocol`_

.. _Python: https://www.python.org/
.. _formatted string literals: https://docs.python.org/3/reference/lexical_analysis.html#f-strings
.. _file system path protocol: https://docs.python.org/3/whatsnew/3.6.html#whatsnew36-pep519


.. _MOHID-CmdGettingTheCode:

Getting the Code
================

.. image:: https://img.shields.io/badge/version%20control-hg-blue.svg
    :target: https://bitbucket.org/midoss/mohid-cmd/
    :alt: Mercurial on Bitbucket

Clone the code and documentation `repository`_ from Bitbucket with:

.. _repository: https://bitbucket.org/midoss/mohid-cmd/

.. code-block:: bash

    $ hg clone ssh://hg@bitbucket.org/midoss/mohid-cmd MOHID-Cmd

or

.. code-block:: bash

    $ hg clone https://your_userid@bitbucket.org/midoss/mohid-cmd MOHID-Cmd

if you don't have `ssh key authentication`_ set up on Bitbucket
(replace :kbd:`you_userid` with you Bitbucket userid,
or copy the link from the :guilabel:`Clone` action pop-up on the `repository`_ page).

.. _ssh key authentication: https://confluence.atlassian.com/bitbucket/set-up-an-ssh-key-728138079.html


.. _MOHID-CmdDevelopmentEnvironment:

Development Environment
=======================

The :kbd:`MOHID-Cmd` package depends on the :kbd:`NEMO-Cmd` package,
so you need to clone the `NEMO-Cmd repo`_
beside your clone of the :kbd:`MOHID-Cmd` `repository`_.

.. _NEMO-Cmd repo: https://bitbucket.org/salishsea/nemo-cmd

Setting up an isolated development environment using `Conda`_ is recommended.
Assuming that you have the `Anaconda Python Distribution`_ or `Miniconda3`_ installed,
you can create and activate an environment called :kbd:`mohid-cmd` that will have all of the Python packages necessary for development,
testing,
and building the documentation with the commands below.

.. _Conda: https://conda.io/en/latest/
.. _Anaconda Python Distribution: https://www.anaconda.com/distribution/
.. _Miniconda3:  https://docs.conda.io/en/latest/miniconda.html

.. code-block:: bash

    $ cd MIDOSS
    $ conda env create -f MOHID-Cmd/env/environment-dev.yaml
    $ source activate mohid-cmd
    (mohid-cmd)$ python3 -m pip install --editable NEMO-Cmd/
    (mohid-cmd)$ python3 -m pip install --editable MOHID-Cmd/

The :kbd:`--editable` option in the :command:`python3 -m pip install` command above installs the packages from the cloned repos via symlinks so that the installed packages will be automatically updated as the repos evolve.

To deactivate the environment use:

.. code-block:: bash

    (mohid-cmd)$ conda deactivate


.. _MOHID-CmdCodingStyle:

Coding Style
============

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://black.readthedocs.io/en/stable/
    :alt: The uncompromising Python code formatter

The :kbd:`MOHID-Cmd` package uses the `black`_ code formatting tool to maintain a coding style that is very close to `PEP 8`_.

.. _black: https://black.readthedocs.io/en/stable/
.. _PEP 8: https://www.python.org/dev/peps/pep-0008/

:command:`black` is installed as part of the :ref:`MOHID-CmdDevelopmentEnvironment` setup.

To run :command:`black` on the entire code-base use:

.. code-block:: bash

    $ cd MOHID-Cmd
    $ conda activate mohid_cmd
    (mohid-cmd)$ black ./

in the repository root directory.
The output looks something like::

  reformatted /media/doug/warehouse/MIDOSS/MOHID-Cmd/docs/conf.py
  All done! ✨ 🍰 ✨
  1 file reformatted, 3 files left unchanged.


.. _MOHID-CmdBuildingTheDocumentation:

Building the Documentation
==========================

.. image:: https://readthedocs.org/projects/mohid-cmd/badge/?version=latest
    :target: https://mohid-cmd.readthedocs.io/en/latest/
    :alt: Documentation Status

The documentation for the :kbd:`MOHID-Cmd` package is written in `reStructuredText`_ and converted to HTML using `Sphinx`_.
Creating a :ref:`MOHID-CmdDevelopmentEnvironment` as described above includes the installation of Sphinx.
Building the documentation is driven by the :file:`docs/Makefile`.
With your :kbd:`salishsea-nowcast` development environment activated,
use:

.. _reStructuredText: http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. _Sphinx: http://www.sphinx-doc.org/en/master/

.. code-block:: bash

    (mohid-cmd)$ (cd docs && make clean html)

to do a clean build of the documentation.
The output looks something like::

  Removing everything under '_build'...
  Running Sphinx v2.2.2
  making output directory... done
  loading intersphinx inventory from https://docs.python.org/objects.inv...
  intersphinx inventory has moved: https://docs.python.org/objects.inv -> https://docs.python.org/3/objects.inv
  building [mo]: targets for 0 po files that are out of date
  building [html]: targets for 5 source files that are out of date
  updating environment: [new config] 5 added, 0 changed, 0 removed
  reading sources... [100%] subcommands
  looking for now-outdated files... none found
  pickling environment... done
  checking consistency... done
  preparing documents... done
  writing output... [100%] subcommands
  generating indices...  genindexdone
  writing additional pages...
  done
  copying static files... ... done
  copying extra files... done
  dumping search index in English (code: en)... done
  dumping object inventory... done
  build succeeded.

  The HTML pages are in _build/html.

The HTML rendering of the docs ends up in :file:`docs/_build/html/`.
You can open the :file:`index.html` file in that directory tree in your browser to preview the results of the build.

If you have write access to the `repository`_ on Bitbucket,
whenever you push changes to Bitbucket the documentation is automatically re-built and rendered at https://mohid-cmd.readthedocs.io/en/latest/.


.. _MOHID-CmdLinkCheckingTheDocumentation:

Link Checking the Documentation
-------------------------------

Sphinx also provides a link checker utility which can be run to find broken or redirected links in the docs.
With your :kbd:`mohid-cmd)` environment activated,
use:

.. code-block:: bash

    (mohid-cmd))$ cd MOHID-Cmd)/docs/
    (mohid-cmd)) docs$ make linkcheck

The output looks something like::

  Running Sphinx v2.2.2
  making output directory... done
  loading pickled environment... done
  building [mo]: targets for 0 po files that are out of date
  building [linkcheck]: targets for 5 source files that are out of date
  updating environment: 0 added, 1 changed, 0 removed
  reading sources... [100%] pkg_development
  looking for now-outdated files... none found
  pickling environment... done
  checking consistency... done
  preparing documents... done
  writing output... [ 20%] index
  (line   23) ok        https://midoss-docs.readthedocs.io/en/latest/
  (line   33) ok        https://docs.openstack.org/cliff/latest/
  (line   33) ok        https://bitbucket.org/salishsea/nemo-cmd
  (line   61) ok        https://bitbucket.org/midoss/docs/src/tip/CONTRIBUTORS.rst
  (line   23) ok        http://www.mohid.com/
  (line   67) ok        https://www.apache.org/licenses/LICENSE-2.0
  writing output... [ 40%] pkg_development
  (line   21) ok        https://docs.python.org/3.7/
  (line   58) ok        https://www.python.org/
  (line   62) ok        https://docs.python.org/3/reference/lexical_analysis.html#f-strings
  (line   64) ok        https://docs.python.org/3/whatsnew/3.6.html#whatsnew36-pep519
  (line   21) ok        https://black.readthedocs.io/en/stable/
  (line   21) ok        https://mohid-cmd.readthedocs.io/en/latest/
  (line   21) ok        https://bitbucket.org/midoss/mohid-cmd/
  (line   21) ok        https://bitbucket.org/midoss/mohid-cmd/issues?status=new&status=open
  (line   74) ok        https://bitbucket.org/midoss/mohid-cmd/
  (line   80) ok        https://bitbucket.org/midoss/mohid-cmd/
  (line  112) ok        https://conda.io/en/latest/
  (line  148) ok        https://www.python.org/dev/peps/pep-0008/
  (line  112) ok        https://docs.conda.io/en/latest/miniconda.html
  (line  180) ok        http://www.sphinx-doc.org/en/master/
  (line  180) ok        http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
  (line  300) ok        https://docs.pytest.org/en/latest/
  (line  112) ok        https://www.anaconda.com/distribution/
  (line  325) ok        https://coverage.readthedocs.io/en/latest/
  (line   21) ok        https://img.shields.io/badge/license-Apache%202-cb2533.svg
  (line   21) ok        https://img.shields.io/badge/python-3.6+-blue.svg
  (line   21) ok        https://img.shields.io/badge/version%20control-hg-blue.svg
  (line   94) ok        https://confluence.atlassian.com/bitbucket/set-up-an-ssh-key-728138079.html
  (line  373) ok        https://bitbucket.org/midoss/mohid-cmd/issues
  (line  142) ok        https://img.shields.io/badge/code%20style-black-000000.svg
  (line   21) ok        https://readthedocs.org/projects/mohid-cmd/badge/?version=latest
  (line  359) ok        https://www.mercurial-scm.org/
  (line  174) ok        https://readthedocs.org/projects/mohid-cmd/badge/?version=latest
  (line   21) ok        https://img.shields.io/badge/code%20style-black-000000.svg
  (line   21) ok        https://img.shields.io/bitbucket/issues/midoss/mohid-cmd.svg
  (line  367) ok        https://img.shields.io/bitbucket/issues/midoss/mohid-cmd.svg
  writing output... [ 60%] run_description_file/index
  (line   23) ok        https://pyyaml.org/wiki/PyYAMLDocumentation
  (line   28) ok        https://bitbucket.org/midoss/midoss-mohid-config/
  writing output... [ 80%] run_description_file/yaml_file
  (line   70) ok        https://bitbucket.org/midoss/midoss-mohid-code/
  writing output... [100%] subcommands

  build succeeded.

  Look for any errors in the above output or in _build/linkcheck/output.txt


.. _MOHID-CmdRunningTheUnitTests:

Running the Unit Tests
======================

The test suite for the :kbd:`MOHID-Cmd` package is in :file:`MOHID-Cmd/tests/`.
The `pytest`_ tool is used for test parametrization and as the test runner for the suite.

.. _pytest: https://docs.pytest.org/en/latest/

With your :kbd:`mohid-cmd` development environment activated,
use:

.. code-block:: bash

    (mohid-cmd)$ cd MOHID-Cmd/
    (mohid-cmd)$ pytest

to run the test suite.
The output looks something like::

  =========================== test session starts ============================
  platform linux -- Python 3.7.3, pytest-5.3.1, py-1.8.0, pluggy-0.13.0
  rootdir: /media/doug/warehouse/MIDOSS/MOHID-Cmd
  collected 84 items

  tests/test_gather.py .....                                            [  5%]
  tests/test_monte_carlo.py ............................                [ 39%]
  tests/test_prepare.py ........................                        [ 67%]
  tests/test_run.py ...........................                         [100%]

  ============================ 84 passed in 2.80s ============================

You can monitor what lines of code the test suite exercises using the `coverage.py`_ tool with the command:

.. _coverage.py: https://coverage.readthedocs.io/en/latest/

.. code-block:: bash

    (mohid-cmd)$ cd MOHID-Cmd/
    (mohid-cmd)$ coverage run -m py.test

and generate a test coverage report with:

.. code-block:: bash

    (mohid-cmd)$ coverage report

to produce a plain text report,
or

.. code-block:: bash

    (mohid-cmd)$ coverage html

to produce an HTML report that you can view in your browser by opening :file:`MOHID-Cmd/htmlcov/index.html`.


.. _MOHID-CmdVersionControlRepository:

Version Control Repository
==========================

.. image:: https://img.shields.io/badge/version%20control-hg-blue.svg
    :target: https://bitbucket.org/midoss/mohid-cmd/
    :alt: Mercurial on Bitbucket

The :kbd:`MOHID-Cmd` package code and documentation source files are available as a `Mercurial`_ repository at https://bitbucket.org/midoss/mohid-cmd/.

.. _Mercurial: https://www.mercurial-scm.org/


.. _MOHID-CmdIssueTracker:

Issue Tracker
=============

.. image:: https://img.shields.io/bitbucket/issues/midoss/mohid-cmd.svg
    :target: https://bitbucket.org/midoss/mohid-cmd/issues?status=new&status=open
    :alt: Issue Tracker

Development tasks,
bug reports,
and enhancement ideas are recorded and managed in the issue tracker at https://bitbucket.org/midoss/mohid-cmd/issues.


License
=======

.. image:: https://img.shields.io/badge/license-Apache%202-cb2533.svg
    :target: https://www.apache.org/licenses/LICENSE-2.0
    :alt: Licensed under the Apache License, Version 2.0

The code and documentation of the MIDOSS-MOHID Command Processor project
are copyright 2019 by the MIDOSS project contributors, The University of British Columbia,
and Dalhousie University.

They are licensed under the Apache License, Version 2.0.
https://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
