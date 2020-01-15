#  Copyright 2018-2020 the MIDOSS project contributors, The University of British Columbia,
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
"""MOHID-Cmd gather sub-command plug-in unit tests.
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import mohid_cmd.gather
import mohid_cmd.main


@pytest.fixture
def gather_cmd():
    return mohid_cmd.gather.Gather(mohid_cmd.main.MohidApp, [])


class TestParser:
    """Unit tests for `mohid gather` sub-command command-line parser.
    """

    def test_get_parser(self, gather_cmd):
        parser = gather_cmd.get_parser("mohid gather")
        assert parser.prog == "mohid gather"

    def test_cmd_description(self, gather_cmd):
        parser = gather_cmd.get_parser("mohid gather")
        assert parser.description.strip().startswith(
            "Gather the results files from the MIDOSS-MOHID run in the present working"
        )

    def test_results_dir_argument(self, gather_cmd):
        parser = gather_cmd.get_parser("mohid gather")
        assert parser._actions[1].dest == "results_dir"
        assert parser._actions[1].metavar == "RESULTS_DIR"
        assert parser._actions[1].type == Path
        assert parser._actions[1].help


class TestTakeAction:
    """Unit tests for `mohid gather` sub-command take_action() method.
    """

    @patch("mohid_cmd.gather.gather", autospec=True)
    def test_take_action(self, m_gather, gather_cmd):
        parsed_args = SimpleNamespace(results_dir=Path("results dir"))
        gather_cmd.take_action(parsed_args)
        m_gather.assert_called_once_with(Path("results dir"))


@pytest.mark.parametrize(
    "res_files, expected",
    (
        (
            {
                Path("Lagrangian_MarathassaCostTS.hdf5"),
                Path("Hydrodynamics_MarathassaCostTS.hdf5"),
            },
            {
                Path("Lagrangian_MarathassaCostTS.hdf5"),
                Path("Hydrodynamics_MarathassaCostTS.hdf5"),
            },
        ),
    ),
)
@patch("mohid_cmd.gather.nemo_cmd.resolved_path", spec=True)
@patch("mohid_cmd.gather.Path.glob", autospec=True)
@patch("mohid_cmd.gather.Path.is_symlink", return_value=True, autospec=True)
@patch("mohid_cmd.gather._move_results", autospec=True)
class TestGather:
    """Unit test for `mohid gather` gather() function.
    """

    def test_gather(
        self, m_mv_results, m_is_link, m_glob, m_rslv_path, res_files, expected, tmpdir
    ):
        p_results_dir = tmpdir.ensure_dir("results_dir")
        symlinks = {Path("winds.hdf5"), Path("currents.hdf5")}
        m_glob.side_effect = (symlinks, res_files)
        mohid_cmd.gather.gather(Path(str(p_results_dir)))
        m_rslv_path.assert_called_once_with(Path(str(p_results_dir)))
        m_rslv_path().mkdir.assert_called_once_with(parents=True, exist_ok=True)
        m_mv_results.assert_called_once_with(m_rslv_path(), symlinks, expected)
