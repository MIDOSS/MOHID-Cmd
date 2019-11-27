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
"""MOHID-Cmd -- MIDOSS-MOHID command processor package
"""
import setuptools


setuptools.setup(
    entry_points={
        # The mohid command:
        "console_scripts": ["mohid = mohid_cmd.main:main"],
        # Sub-command plug-ins:
        "mohid.app": [
            "gather = mohid_cmd.gather:Gather",
            "monte-carlo = mohid_cmd.monte_carlo:MonteCarlo",
            "prepare = mohid_cmd.prepare:Prepare",
            "run = mohid_cmd.run:Run",
        ],
    }
)
