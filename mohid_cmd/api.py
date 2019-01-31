#  Copyright 2018-2019 the MIDOSS project contributors, The University of British Columbia,
#  and Dalhousie University.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""MIDOSS-MOHID command processor API

Application programming interface for the MIDOSS-MOHID command processor.
Provides Python function interfaces to command processor sub-commands
for use in other sub-command processor _modules,
and by other software.
"""
import logging

from mohid_cmd import prepare as prepare_plugin

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(name)s %(levelname)s: %(message)s")
handler.setFormatter(formatter)
log.addHandler(handler)


def prepare(run_desc_file):
    """Prepare a MIDOSS-MOHID run.

    A temporary run directory is created with a unique name composed of the run id
    and an ISO-format date/time stamp.
    Symbolic links and file copies are created in that directory based on the
    files and directories specified in the run description YAML file for a
    MIDOSS-MOHID run.
    The output of :command:`hg parents` is recorded in the directory for the
    MIDOSS-MOHID code and MIDOSS-MOHID-config repos that the symlinks point to.
    The path to the temporary run directory is returned.

    :param run_desc_file: File path/name of the YAML run description file.
    :type run_desc_file: :py:class:`pathlib.Path`

    :returns: Path of the temporary run directory
    :rtype: :py:class:`pathlib.Path`
    """
    return prepare_plugin.prepare(run_desc_file)
