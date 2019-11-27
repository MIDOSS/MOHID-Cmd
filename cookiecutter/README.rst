**********************************************************
MIDOSS-MOHID Monte Carlo Runs GLOST Job Directory Template
**********************************************************

This directory is a `cookiecutter`_ template for `GLOST`_ job directories for MIDOSS project Monte Carlo runs of MOHID.
It is used by the :ref:`mohid-monte-carlo`.

The :file:`cookiecutter.json` file contains the template variables and their default values.
The defaults are (mostly) overridden by values calculated by the :ref:`mohid-monte-carlo`.
Sadly,
comments are not allowed in JSON files,
so you will have to guess the meaning of the template variables from their names and values,
or read the cdoe in the :file:`mohid_cmd/monte_carlo.py` module to learn more about them.

The :file:`{{cookiecutter.job_dir}}` directory is the temporary run directory template.
The rendered temporary run directory will have the name given by the :kbd:`job_dir` template variable.

Please see the `cookiecutter`_ docs for more details of the template structure,
template variables,
and how the template rendering process works.

.. _cookiecutter: https://cookiecutter.readthedocs.io/en/latest/index.html
.. _GLOST: https://docs.computecanada.ca/wiki/GLOST
