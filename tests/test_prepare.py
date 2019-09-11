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
import textwrap
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import call, Mock, patch

import nemo_cmd.prepare
import pytest
import yaml

import mohid_cmd.prepare


@pytest.fixture
def prepare_cmd():
    return mohid_cmd.prepare.Prepare(Mock(spec=True), [])


@pytest.fixture()
def run_desc(tmpdir):
    p_run_desc = tmpdir.join("mohid.yaml")
    p_run_desc.write(
        textwrap.dedent(
            """\
            run_id: MarathassaConstTS
        
            paths:
              mohid repo: MIDOSS-MOHID/
              runs directory: runs/
        
            forcing:
              winds.hdf5: MIDOSS/forcing/HRDPS/hrdps_20181211_20181218.hdf5
        
            bathymetry: MIDOSS-MOHID-config/SalishSeaCast/SalishSeaCast_bathymetry.dat
        
            run data files:
              IN_MODEL: MIDOSS-MOHID-config/MarathassaConstTS/Model.dat
              PARTIC_DATA: MIDOSS-MOHID-config/MarathassaConstTS/Lagrangian_DieselFuel_refined.dat
              DOMAIN: MIDOSS-MOHID-config/SalishSeaCast/Geometry.dat
              SURF_DAT: MIDOSS-MOHID-config/SalishSeaCast/Atmosphere.dat
              IN_DAD3D: MIDOSS-MOHID-config/SalishSeaCast/Hydrodynamic.dat
              BOT_DAT: MIDOSS-MOHID-config/SalishSeaCast/InterfaceSedimentWater.dat
              AIRW_DAT: MIDOSS-MOHID-config/SalishSeaCast/InterfaceWaterAir.dat
              IN_TIDES: MIDOSS-MOHID-config/SalishSeaCast/Tide.dat
              IN_TURB: MIDOSS-MOHID-config/SalishSeaCast/Turbulence.dat
              DISPQUAL: MIDOSS-MOHID-config/SalishSeaCast/WaterProperties.dat
              WAVES_DAT: MIDOSS-MOHID-config/SalishSeaCast/Waves.dat
        
            vcs revisions:
              hg:
                - MIDOSS-MOHID-config
            """
        )
    )
    with open(str(p_run_desc), "rt") as f:
        run_desc = yaml.safe_load(f)
    return run_desc


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

    def test_parsed_args_defaults(self, prepare_cmd):
        parser = prepare_cmd.get_parser("mohid prepare")
        parsed_args = parser.parse_args(["foo.yaml"])
        assert parsed_args.desc_file == Path("foo.yaml")
        assert not parsed_args.quiet

    @pytest.mark.parametrize("flag", ["-q", "--quiet"])
    def test_parsed_args_options(self, flag, prepare_cmd):
        parser = prepare_cmd.get_parser("mohid prepare")
        parsed_args = parser.parse_args(["foo.yaml", flag])
        assert parsed_args.quiet is True


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
        parsed_args = SimpleNamespace(desc_file="foo.yaml", quiet=False)
        tmp_run_dir = prepare_cmd.take_action(parsed_args)
        m_logger.info.assert_called_once_with(
            "Created temporary run directory: foo_2018-12-10T124643.123456-0800"
        )
        assert tmp_run_dir == Path("foo_2018-12-10T124643.123456-0800")

    def test_quiet(self, m_prepare, m_logger, prepare_cmd):
        parsed_args = SimpleNamespace(desc_file="foo.yaml", quiet=True)
        prepare_cmd.take_action(parsed_args)
        assert not m_logger.info.called


@patch("nemo_cmd.prepare.load_run_desc", spec=True)
@patch("mohid_cmd.prepare._check_mohid_exec", spec=True)
@patch("nemo_cmd.prepare.make_run_dir", spec=True)
@patch("nemo_cmd.prepare.shutil.copy2", autospec=True)
@patch("mohid_cmd.prepare._make_forcing_links", spec=True)
@patch("mohid_cmd.prepare._make_nomfich", spec=True)
@patch("mohid_cmd.prepare._record_vcs_revisions", spec=True)
class TestPrepare:
    """Unit test for `mohid prepare` prepare() function.
    """

    def test_prepare(
        self,
        m_rec_vcs_revs,
        m_mk_nomfich,
        m_mk_frc_lnks,
        m_copy2,
        m_mk_run_dir,
        m_chk_mohid_exe,
        m_ld_run_desc,
    ):
        with patch("mohid_cmd.prepare.Path.symlink_to") as m_ln:
            tmp_run_dir = mohid_cmd.prepare.prepare(Path("foo.yaml"))
        m_ld_run_desc.assert_called_once_with(Path("foo.yaml"))
        m_chk_mohid_exe.assert_called_once_with(m_ld_run_desc())
        m_mk_run_dir.assert_called_once_with(m_ld_run_desc())
        (m_mk_run_dir() / m_chk_mohid_exe().name).symlink_to.assert_called_once_with(
            m_chk_mohid_exe()
        )
        m_copy2.assert_called_once_with(Path("foo.yaml"), m_mk_run_dir() / "foo.yaml")
        m_mk_frc_lnks.assert_called_once_with(m_ld_run_desc(), m_mk_run_dir())
        m_mk_nomfich.assert_called_once_with(m_ld_run_desc(), m_mk_run_dir())
        m_rec_vcs_revs.assert_called_once_with(m_ld_run_desc(), m_mk_run_dir())
        assert tmp_run_dir == m_mk_run_dir()


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

    def test_mohid_exe_not_found(self, m_logger, tmpdir, run_desc):
        p_mohid_repo = tmpdir.ensure_dir("MIDOSS-MOHID/")
        with patch.dict(run_desc["paths"], {"mohid repo": str(p_mohid_repo)}):
            with pytest.raises(SystemExit):
                mohid_cmd.prepare._check_mohid_exec(run_desc)


@patch("mohid_cmd.prepare.logger", autospec=True)
@patch("nemo_cmd.prepare.remove_run_dir", autospec=True)
class TestMakeForcingLinks:
    """Unit tests for `mohid prepare` _make_forcing_links() function.
    """

    def test_no_link_path(self, m_rm_run_dir, m_logger, run_desc):
        with pytest.raises(SystemExit):
            mohid_cmd.prepare._make_forcing_links(run_desc, Path("tmp_run_dir"))
        m_logger.error.assert_called_once_with(
            f'{run_desc["forcing"]["winds.hdf5"]} not found; cannot create symlink - '
            f"please check the forcing paths and file names in your run description file"
        )
        m_rm_run_dir.assert_called_once_with(Path("tmp_run_dir"))

    def test_make_forcing_links(self, m_rm_run_dir, m_logger, run_desc, tmpdir):
        links = {
            link_name: tmpdir.ensure(source)
            for link_name, source in run_desc["forcing"].items()
        }
        p_tmp_run_dir = tmpdir.ensure_dir("tmp_run_dir")
        with patch.dict(run_desc["forcing"], links):
            mohid_cmd.prepare._make_forcing_links(run_desc, Path(str(p_tmp_run_dir)))
        for link_name in run_desc["forcing"]:
            assert p_tmp_run_dir.join(link_name).check(link=True)
        assert not m_logger.error.called
        assert not m_rm_run_dir.called


@patch("mohid_cmd.prepare.nemo_cmd.prepare.logger", autospec=True)
class TestMakeNomfich:
    """Unit tests for `mohid prepare` _make_nomfich() function.
    """

    def test_no_bathymetry_key(self, m_logger, run_desc):
        with pytest.raises(SystemExit):
            mohid_cmd.prepare._make_nomfich({}, Path("tmp_run_dir"))
        m_logger.error.assert_called_once_with(
            '"bathymetry" key not found - please check your run description YAML file'
        )

    def test_bathymetry_file_not_found(self, m_logger, run_desc):
        with pytest.raises(SystemExit):
            mohid_cmd.prepare._make_nomfich(run_desc, Path("tmp_run_dir"))
        m_logger.error.assert_called_once_with(
            f'{Path(run_desc["bathymetry"]).resolve()} path from "bathymetry" key not found - '
            f"please check your run description YAML file"
        )

    @patch("mohid_cmd.prepare.Path.mkdir", autospec=True)
    def test_make_results_dir(self, m_mkdir, m_logger, tmpdir, run_desc):
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

    def test_nomfich_file(self, m_logger, tmpdir, run_desc):
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


class TestRecordVCSRevisions:
    """Unit tests for `mohid prepare` _record_vcs_revisions() function.
    """

    def test_no_paths_forcing_key(self, run_desc):
        with pytest.raises(SystemExit):
            mohid_cmd.prepare._record_vcs_revisions(run_desc, Path("run_dir"))

    @patch("nemo_cmd.prepare.write_repo_rev_file")
    def test_write_repo_rev_file_mohid_repo(self, m_write, tmpdir, run_desc):
        p_tmp_run_dir = tmpdir.ensure_dir("tmp_run_dir")
        p_mohid_repo = tmpdir.ensure(run_desc["paths"]["mohid repo"])
        p_run_desc = patch.dict(
            run_desc,
            {"paths": {"mohid repo": str(p_mohid_repo)}, "vcs revisions": {"hg": []}},
        )
        with p_run_desc:
            mohid_cmd.prepare._record_vcs_revisions(run_desc, Path(str(p_tmp_run_dir)))
        m_write.assert_called_once_with(
            Path(str(p_mohid_repo)),
            Path(str(p_tmp_run_dir)),
            nemo_cmd.prepare.get_hg_revision,
        )

    @patch("nemo_cmd.prepare.write_repo_rev_file")
    def test_write_repo_rev_file_hg_repo(self, m_write, tmpdir, run_desc):
        p_tmp_run_dir = tmpdir.ensure_dir("tmp_run_dir")
        p_mohid_repo = tmpdir.ensure(run_desc["paths"]["mohid repo"])
        p_hg_repo = tmpdir.ensure(run_desc["vcs revisions"]["hg"][0])
        p_run_desc = patch.dict(
            run_desc,
            {
                "paths": {"mohid repo": str(p_mohid_repo)},
                "vcs revisions": {"hg": [str(p_hg_repo)]},
            },
        )
        with p_run_desc:
            mohid_cmd.prepare._record_vcs_revisions(run_desc, Path(str(p_tmp_run_dir)))
        assert m_write.call_args_list[1] == call(
            Path(str(p_hg_repo)),
            Path(str(p_tmp_run_dir)),
            nemo_cmd.prepare.get_hg_revision,
        )
