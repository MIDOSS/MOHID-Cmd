# Copyright 2018-2019 the MIDOSS project contributors, The University of British Columbia,
# and Dalhousie University.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""MOHID-Cmd prepare sub-command plug-in unit tests.
"""
import logging
import textwrap
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import call, patch

import arrow
import nemo_cmd.prepare
import pytest

import mohid_cmd.main
import mohid_cmd.prepare


@pytest.fixture
def prepare_cmd():
    return mohid_cmd.prepare.Prepare(mohid_cmd.main.MohidApp, [])


class TestParser:
    """Unit tests for `mohid prepare` sub-command command-line parser.
    """

    def test_get_parser(self, prepare_cmd):
        parser = prepare_cmd.get_parser("mohid prepare")
        assert parser.prog == "mohid prepare"

    def test_cmd_description(self, prepare_cmd):
        parser = prepare_cmd.get_parser("mohid prepare")
        assert parser.description.startswith(
            "Set up the MIDOSS-MOHID run described in DESC_FILE"
        )

    def test_desc_file_argument(self, prepare_cmd):
        parser = prepare_cmd.get_parser("mohid prepare")
        assert parser._actions[1].dest == "desc_file"
        assert parser._actions[1].metavar == "DESC_FILE"
        assert parser._actions[1].type == Path
        assert parser._actions[1].help

    def test_quiet_argument(self, prepare_cmd):
        parser = prepare_cmd.get_parser("mohid prepare")
        assert parser._actions[2].dest == "quiet"
        assert parser._actions[2].option_strings == ["-q", "--quiet"]
        assert parser._actions[2].const is True
        assert parser._actions[2].default is False
        assert parser._actions[2].help

    def test_tmp_run_dir_option(self, prepare_cmd):
        parser = prepare_cmd.get_parser("mohid prepare")
        assert parser._actions[3].dest == "tmp_run_dir"
        assert parser._actions[3].option_strings == ["--tmp-run-dir"]
        assert parser._actions[3].default == ""
        assert parser._actions[3].help

    def test_parsed_args(self, prepare_cmd):
        parser = prepare_cmd.get_parser("mohid prepare")
        parsed_args = parser.parse_args(["foo.yaml"])
        assert parsed_args.desc_file == Path("foo.yaml")

    def test_parsed_args_option_defaults(self, prepare_cmd):
        parser = prepare_cmd.get_parser("mohid prepare")
        parsed_args = parser.parse_args(["foo.yaml"])
        assert parsed_args.quiet is False

    @pytest.mark.parametrize("flag", ["-q", "--quiet"])
    def test_parsed_args_quiet_options(self, flag, prepare_cmd):
        parser = prepare_cmd.get_parser("mohid prepare")
        parsed_args = parser.parse_args(["foo.yaml", flag])
        assert parsed_args.quiet is True

    def test_parsed_args_tmp_run_dir_option(self, prepare_cmd):
        parser = prepare_cmd.get_parser("mohid prepare")
        parsed_args = parser.parse_args(["foo.yaml", "--tmp-run-dir", "tmp_run_dir"])
        assert parsed_args.tmp_run_dir == "tmp_run_dir"


@patch("mohid_cmd.prepare.logger", autospec=True)
@patch(
    "mohid_cmd.prepare.prepare",
    return_value=Path("foo_2018-12-10T124643.123456-0800"),
    autospec=True,
)
class TestTakeAction:
    """Unit tests for `mohid prepare` sub-command take_action() method.
    """

    def test_return_tmp_run_dir(self, m_prepare, m_logger, prepare_cmd):
        parsed_args = SimpleNamespace(desc_file="foo.yaml", quiet=False, tmp_run_dir="")
        tmp_run_dir = prepare_cmd.take_action(parsed_args)
        m_logger.info.assert_called_once_with(
            "Created temporary run directory: foo_2018-12-10T124643.123456-0800"
        )
        assert tmp_run_dir == Path("foo_2018-12-10T124643.123456-0800")

    def test_quiet(self, m_prepare, m_logger, prepare_cmd):
        parsed_args = SimpleNamespace(desc_file="foo.yaml", quiet=True, tmp_run_dir="")
        prepare_cmd.take_action(parsed_args)
        assert not m_logger.info.called


@patch("nemo_cmd.prepare.shutil.copy2", autospec=True)
@patch("mohid_cmd.prepare._make_forcing_links", spec=True)
@patch("mohid_cmd.prepare._make_nomfich", spec=True)
@patch("mohid_cmd.prepare.nemo_cmd.prepare.write_repo_rev_file", spec=True)
@patch("mohid_cmd.prepare.nemo_cmd.prepare.record_vcs_revisions", spec=True)
class TestPrepare:
    """Unit tests for `mohid prepare` prepare() function.
    """

    def test_prepare(
        self,
        m_rec_vcs_revs,
        m_write_vcs_revs,
        m_mk_nomfich,
        m_mk_frc_lnks,
        m_copy2,
        run_desc,
        tmp_path,
        monkeypatch,
    ):
        def mock_make_run_dir(*args):
            tmp_run_dir = (
                tmp_path
                / "runs_dir"
                / "MarathassaConstTS_2019-11-23T203918.370737-0800"
            )
            tmp_run_dir.mkdir()
            return tmp_run_dir

        monkeypatch.setattr(mohid_cmd.prepare, "_make_run_dir", mock_make_run_dir)

        tmp_run_dir = mohid_cmd.prepare.prepare(tmp_path / "mohid.yaml")
        assert (tmp_run_dir / "MohidWater.exe").is_symlink()
        m_copy2.assert_called_once_with(
            tmp_path / "mohid.yaml", tmp_run_dir / "mohid.yaml"
        )
        m_mk_frc_lnks.assert_called_once_with(run_desc, tmp_run_dir)
        m_mk_nomfich.assert_called_once_with(run_desc, tmp_run_dir)
        m_write_vcs_revs.assert_called_once_with(
            tmp_path / "MIDOSS-MOHID-CODE",
            tmp_run_dir,
            nemo_cmd.prepare.get_hg_revision,
        )
        m_rec_vcs_revs.assert_called_once_with(run_desc, tmp_run_dir)
        assert (
            tmp_run_dir
            == tmp_path / "runs_dir" / "MarathassaConstTS_2019-11-23T203918.370737-0800"
        )

    def test_prepare_w_tmp_run_dir(
        self,
        m_rec_vcs_revs,
        m_write_vcs_revs,
        m_mk_nomfich,
        m_mk_frc_lnks,
        m_copy2,
        run_desc,
        tmp_path,
    ):
        tmp_run_dir = mohid_cmd.prepare.prepare(tmp_path / "mohid.yaml", "tmp_run_dir")
        assert (tmp_run_dir / "MohidWater.exe").is_symlink()
        m_copy2.assert_called_once_with(
            tmp_path / "mohid.yaml", tmp_run_dir / "mohid.yaml"
        )
        m_mk_frc_lnks.assert_called_once_with(run_desc, tmp_run_dir)
        m_mk_nomfich.assert_called_once_with(run_desc, tmp_run_dir)
        m_write_vcs_revs.assert_called_once_with(
            tmp_path / "MIDOSS-MOHID-CODE",
            tmp_run_dir,
            nemo_cmd.prepare.get_hg_revision,
        )
        m_rec_vcs_revs.assert_called_once_with(run_desc, tmp_run_dir)
        assert tmp_run_dir == (tmp_path / "runs_dir") / "tmp_run_dir"


@patch("mohid_cmd.prepare.logger", autospec=True)
class TestCheckMohidExec:
    """Unit tests for `mohid prepare` _check_mohid_exec() function.
    """

    def test_mohid_exe(self, m_logger, tmpdir, run_desc):
        p_mohid_repo = tmpdir.ensure_dir("MIDOSS-MOHID/")
        p_mohid_exe = p_mohid_repo.ensure("Solutions/linux/bin/MohidWater.exe")
        with patch.dict(run_desc["paths"], {"mohid repo": str(p_mohid_repo)}):
            mohid_exe = mohid_cmd.prepare._check_mohid_exec(run_desc)
        assert mohid_exe == Path(str(p_mohid_exe))
        assert not m_logger.error.called

    def test_mohid_exe_not_found(self, m_logger, run_desc, monkeypatch):
        monkeypatch.setitem(run_desc["paths"], "mohid repo", "not mohid repo")
        with pytest.raises(SystemExit):
            mohid_cmd.prepare._check_mohid_exec(run_desc)


class TestMakeRunDir:
    """Unit tests for `mohid prepare` _make_run_dir() function.
    """

    def test_timestamp_run_dir(self, run_desc, monkeypatch):
        def mock_arrow_now():
            return arrow.get("2019-11-24T094803.201666-0800")

        monkeypatch.setattr(nemo_cmd.prepare.arrow, "now", mock_arrow_now)

        tmp_run_dir = mohid_cmd.prepare._make_run_dir(run_desc, tmp_run_dir="")
        expected = (
            Path(run_desc["paths"]["runs directory"])
            / "MarathassaConstTS_2019-11-24T094803.201666-0800"
        )
        assert tmp_run_dir == expected

    def test_named_run_dir(self, run_desc):
        tmp_run_dir = mohid_cmd.prepare._make_run_dir(run_desc, tmp_run_dir="foobar")
        assert tmp_run_dir == Path(run_desc["paths"]["runs directory"]) / "foobar"


class TestMakeForcingLinks:
    """Unit tests for `mohid prepare` _make_forcing_links() function.
    """

    def test_no_link_path(self, run_desc, caplog, tmp_path, monkeypatch):
        monkeypatch.setitem(run_desc["forcing"], "winds.hdf5", "not a file")

        tmp_run_dir = tmp_path / "tmp_run_dir"
        tmp_run_dir.mkdir()
        caplog.set_level(logging.ERROR)
        with pytest.raises(SystemExit):
            mohid_cmd.prepare._make_forcing_links(run_desc, tmp_run_dir)
        assert caplog.records[0].levelname == "ERROR"
        expected = (
            f'{run_desc["forcing"]["winds.hdf5"]} not found; cannot create symlink - '
            f"please check the forcing paths and file names in your run description file"
        )
        assert caplog.messages[0] == expected
        assert not tmp_run_dir.exists()

    def test_make_forcing_links(self, run_desc, caplog, tmp_path):
        tmp_run_dir = tmp_path / "tmp_run_dir"
        tmp_run_dir.mkdir()
        caplog.set_level(logging.ERROR)
        mohid_cmd.prepare._make_forcing_links(run_desc, tmp_run_dir)
        for link_name in run_desc["forcing"]:
            (tmp_run_dir / link_name).is_symlink()
        assert not caplog.records
        assert tmp_run_dir.exists()


class TestMakeNomfich:
    """Unit tests for `mohid prepare` _make_nomfich() function.
    """

    def test_no_bathymetry_key(self, run_desc, caplog, monkeypatch):
        monkeypatch.delitem(run_desc, "bathymetry")
        caplog.set_level(logging.ERROR)
        with pytest.raises(SystemExit):
            mohid_cmd.prepare._make_nomfich(run_desc, Path("tmp_run_dir"))
        assert caplog.records[0].levelname == "ERROR"
        expected = (
            '"bathymetry" key not found - please check your run description YAML file'
        )
        assert caplog.messages[0] == expected

    def test_bathymetry_file_not_found(self, run_desc, caplog, tmp_path, monkeypatch):
        monkeypatch.setitem(
            run_desc, "bathymetry", tmp_path / "MIDOSS-MOHID-grid" / "not_bathy.dat"
        )
        caplog.set_level(logging.ERROR)
        with pytest.raises(SystemExit):
            mohid_cmd.prepare._make_nomfich(run_desc, Path("tmp_run_dir"))
        assert caplog.records[0].levelname == "ERROR"
        expected = (
            f'{tmp_path / "MIDOSS-MOHID-grid"/"not_bathy.dat"} path from "bathymetry" key not found - '
            f"please check your run description YAML file"
        )
        assert caplog.messages[0] == expected

    @patch("mohid_cmd.prepare.Path.mkdir", autospec=True)
    def test_make_results_dir(self, m_mkdir, tmpdir, run_desc):
        p_tmp_run_dir = tmpdir.ensure_dir("tmp_run_dir")
        p_bathy = tmpdir.ensure(run_desc["bathymetry"])
        p_run_files = {
            key: tmpdir.ensure(path) for key, path in run_desc["run data files"].items()
        }
        p_run_desc = patch.dict(
            run_desc,
            {
                "bathymetry": str(p_bathy),
                "run data files": {key: str(path) for key, path in p_run_files.items()},
            },
        )
        with p_run_desc:
            mohid_cmd.prepare._make_nomfich(run_desc, Path(str(p_tmp_run_dir)))
        assert m_mkdir.called

    def test_nomfich_file(self, tmpdir, run_desc):
        p_tmp_run_dir = tmpdir.ensure_dir("tmp_run_dir")
        p_bathy = tmpdir.ensure(run_desc["bathymetry"])
        p_run_files = {
            key: tmpdir.ensure(path) for key, path in run_desc["run data files"].items()
        }
        p_run_desc = patch.dict(
            run_desc,
            {
                "bathymetry": str(p_bathy),
                "run data files": {key: str(path) for key, path in p_run_files.items()},
            },
        )
        with p_run_desc:
            mohid_cmd.prepare._make_nomfich(run_desc, Path(str(p_tmp_run_dir)))
        with p_tmp_run_dir.join("nomfich.dat").open("rt") as f:
            nomfich = f.read()
        expected = textwrap.dedent(
            f"""\
            IN_BATIM    : {str(p_bathy)}
            ROOT        : {str(p_tmp_run_dir.join("res"))}
            IN_MODEL    : {str(p_run_files["IN_MODEL"])}
            PARTIC_DATA : {str(p_run_files["PARTIC_DATA"])}
            PARTIC_HDF  : {str(p_tmp_run_dir.join("res/Lagrangian_DieselFuel_refined_MarathassaConstTS.hdf"))}
            DOMAIN      : {str(p_run_files["DOMAIN"])}
            SURF_DAT    : {str(p_run_files["SURF_DAT"])}
            SURF_HDF    : {str(p_tmp_run_dir.join("res/Atmosphere_MarathassaConstTS.hdf"))}
            IN_DAD3D    : {str(p_run_files["IN_DAD3D"])}
            BOT_DAT     : {str(p_run_files["BOT_DAT"])}
            AIRW_DAT    : {str(p_run_files["AIRW_DAT"])}
            AIRW_HDF    : {str(p_tmp_run_dir.join("res/InterfaceWaterAir_MarathassaConstTS.hdf"))}
            IN_TIDES    : {str(p_run_files["IN_TIDES"])}
            IN_TURB     : {str(p_run_files["IN_TURB"])}
            TURB_HDF    : {str(p_tmp_run_dir.join("res/Turbulence_MarathassaConstTS.hdf"))}
            DISPQUAL    : {str(p_run_files["DISPQUAL"])}
            EUL_HDF     : {str(p_tmp_run_dir.join("res/WaterProperties_MarathassaConstTS.hdf"))}
            WAVES_DAT   : {str(p_run_files["WAVES_DAT"])}
            WAVES_HDF   : {str(p_tmp_run_dir.join("res/Waves_MarathassaConstTS.hdf"))}
            """
        )
        assert nomfich == expected
