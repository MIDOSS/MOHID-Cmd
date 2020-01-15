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
"""MOHID-Cmd run sub-command plug-in unit tests.
"""
import logging
import textwrap
from pathlib import Path
import subprocess
from types import SimpleNamespace
from unittest.mock import patch, call

import attr
import pytest

import mohid_cmd.main
import mohid_cmd.prepare
import mohid_cmd.run


@pytest.fixture
def run_cmd():
    return mohid_cmd.run.Run(mohid_cmd.main.MohidApp, [])


class TestParser:
    """Unit tests for `mohid run` sub-command command-line parser.
    """

    def test_get_parser(self, run_cmd):
        parser = run_cmd.get_parser("mohid run")
        assert parser.prog == "mohid run"

    def test_cmd_description(self, run_cmd):
        parser = run_cmd.get_parser("mohid run")
        assert parser.description.strip().startswith(
            "Prepare, execute, and gather the results from a MIDOSS-MOHID"
        )

    def test_desc_file_argument(self, run_cmd):
        parser = run_cmd.get_parser("mohid run")
        assert parser._actions[1].dest == "desc_file"
        assert parser._actions[1].metavar == "DESC_FILE"
        assert parser._actions[1].type == Path
        assert parser._actions[1].help

    def test_results_dir_argument(self, run_cmd):
        parser = run_cmd.get_parser("mohid run")
        assert parser._actions[2].dest == "results_dir"
        assert parser._actions[2].metavar == "RESULTS_DIR"
        assert parser._actions[2].type == Path
        assert parser._actions[2].help

    def test_no_submit_option(self, run_cmd):
        parser = run_cmd.get_parser("mohid run")
        assert parser._actions[3].dest == "no_submit"
        assert parser._actions[3].option_strings == ["--no-submit"]
        assert parser._actions[3].const is True
        assert parser._actions[3].default is False
        assert parser._actions[3].help

    def test_quiet_option(self, run_cmd):
        parser = run_cmd.get_parser("mohid run")
        assert parser._actions[4].dest == "quiet"
        assert parser._actions[4].option_strings == ["-q", "--quiet"]
        assert parser._actions[4].const is True
        assert parser._actions[4].default is False
        assert parser._actions[4].help

    def test_tmp_run_dir_option(self, run_cmd):
        parser = run_cmd.get_parser("mohid run")
        assert parser._actions[5].dest == "tmp_run_dir"
        assert parser._actions[5].option_strings == ["--tmp-run-dir"]
        assert parser._actions[5].default == ""
        assert parser._actions[5].help

    def test_parsed_args(self, run_cmd):
        parser = run_cmd.get_parser("mohid run")
        parsed_args = parser.parse_args(["foo.yaml", "results/foo/"])
        assert parsed_args.desc_file == Path("foo.yaml")
        assert parsed_args.results_dir == Path("results/foo/")

    def test_parsed_args_option_defaults(self, run_cmd):
        parser = run_cmd.get_parser("mohid run")
        parsed_args = parser.parse_args(["foo.yaml", "results/foo/"])
        assert parsed_args.no_submit is False
        assert parsed_args.quiet is False
        assert parsed_args.tmp_run_dir == ""

    @pytest.mark.parametrize("flag", ["-q", "--quiet"])
    def test_parsed_args_quiet_options(self, flag, run_cmd):
        parser = run_cmd.get_parser("mohid run")
        parsed_args = parser.parse_args(["foo.yaml", "results/foo/", flag])
        assert parsed_args.quiet is True

    def test_parsed_args_no_submit_option(self, run_cmd):
        parser = run_cmd.get_parser("mohid run")
        parsed_args = parser.parse_args(["foo.yaml", "results/foo/", "--no-submit"])
        assert parsed_args.no_submit is True

    def test_parsed_args_tmp_run_dir_option(self, run_cmd):
        parser = run_cmd.get_parser("mohid run")
        parsed_args = parser.parse_args(
            ["foo.yaml", "results/foo/", "--tmp-run-dir", "tmp_run_dir"]
        )
        assert parsed_args.tmp_run_dir == "tmp_run_dir"


class TestTakeAction:
    """Unit tests for `mohid run` sub-command take_action() method.
    """

    @staticmethod
    @pytest.fixture
    def mock_write_repo_rev_file(monkeypatch):
        def mock_write_repo_rev_file(*args):
            pass

        monkeypatch.setattr(
            mohid_cmd.prepare.nemo_cmd.prepare,
            "write_repo_rev_file",
            mock_write_repo_rev_file,
        )

    @staticmethod
    @pytest.fixture
    def mock_record_vcs_revisions(monkeypatch):
        def mock_record_vcs_revisions(*args):
            pass

        monkeypatch.setattr(
            mohid_cmd.prepare.nemo_cmd.prepare,
            "record_vcs_revisions",
            mock_record_vcs_revisions,
        )

    @staticmethod
    @pytest.fixture
    def mock_subprocess_run(monkeypatch):
        def mock_subprocess_run(*args, **kwargs):
            @attr.s
            class CompletedProcess:
                stdout = attr.ib(default="Submitted batch job 12345678")

            return CompletedProcess()

        monkeypatch.setattr(mohid_cmd.run.subprocess, "run", mock_subprocess_run)

    def test_take_action(
        self,
        run_cmd,
        run_desc,
        mock_write_repo_rev_file,
        mock_record_vcs_revisions,
        mock_subprocess_run,
        caplog,
        tmp_path,
        monkeypatch,
    ):
        desc_file = tmp_path / "mohid.yaml"
        results_dir = tmp_path / "results_dir"
        parsed_args = SimpleNamespace(
            desc_file=desc_file,
            results_dir=results_dir,
            no_submit=False,
            quiet=False,
            tmp_run_dir="",
        )
        caplog.set_level(logging.INFO)
        run_cmd.take_action(parsed_args)
        assert caplog.records[0].levelname == "INFO"
        assert caplog.messages[2] == "Submitted batch job 12345678"

    def test_take_action_quiet(
        self,
        run_cmd,
        run_desc,
        mock_write_repo_rev_file,
        mock_record_vcs_revisions,
        mock_subprocess_run,
        caplog,
        tmp_path,
        monkeypatch,
    ):
        desc_file = tmp_path / "mohid.yaml"
        results_dir = tmp_path / "results_dir"
        parsed_args = SimpleNamespace(
            desc_file=desc_file,
            results_dir=results_dir,
            no_submit=False,
            quiet=True,
            tmp_run_dir="",
        )
        caplog.set_level(logging.INFO)
        run_cmd.take_action(parsed_args)
        assert not caplog.records

    def test_take_action_no_submit(
        self,
        run_cmd,
        run_desc,
        mock_write_repo_rev_file,
        mock_record_vcs_revisions,
        caplog,
        tmp_path,
    ):
        desc_file = tmp_path / "mohid.yaml"
        results_dir = tmp_path / "results_dir"
        parsed_args = SimpleNamespace(
            desc_file=desc_file,
            results_dir=results_dir,
            no_submit=True,
            quiet=False,
            tmp_run_dir="",
        )
        caplog.set_level(logging.INFO)
        run_cmd.take_action(parsed_args)
        assert len(caplog.records) == 2


@patch("mohid_cmd.run.subprocess.run", autospec=True)
@patch("mohid_cmd.run.nemo_cmd.resolved_path", spec=True)
@patch("mohid_cmd.run._build_run_script", return_value="script", autospec=True)
@patch("mohid_cmd.run.nemo_cmd.prepare.load_run_desc", spec=True)
@patch("mohid_cmd.run.mohid_cmd.prepare.prepare", spec=True)
class TestRun:
    """Unit tests for `mohid run` run() function.
    """

    def test_run_submit(
        self, m_prepare, m_ld_run_desc, m_bld_run_script, m_rslv_path, m_run, tmpdir
    ):
        p_tmp_run_dir = tmpdir.ensure_dir("tmp_run_dir")
        m_prepare.return_value = Path(str(p_tmp_run_dir))
        p_results_dir = tmpdir.ensure_dir("results_dir")
        m_run().stdout = "submit_job_msg"
        submit_job_msg = mohid_cmd.run.run(Path("mohid.yaml"), Path(str(p_results_dir)))
        m_prepare.assert_called_once_with(Path("mohid.yaml"), "")
        m_ld_run_desc.assert_called_once_with(Path("mohid.yaml"))
        m_rslv_path.assert_called_once_with(Path(str(p_results_dir)))
        m_bld_run_script.assert_called_once_with(
            m_ld_run_desc(), Path("mohid.yaml"), m_rslv_path(), m_prepare()
        )
        m_rslv_path().mkdir.assert_called_once_with(parents=True, exist_ok=True)
        assert m_run.call_args_list[1] == call(
            ["sbatch", str(p_tmp_run_dir.join("MOHID.sh"))],
            check=True,
            universal_newlines=True,
            stdout=subprocess.PIPE,
        )
        assert submit_job_msg == "submit_job_msg"

    def test_run_no_submit(
        self, m_prepare, m_ld_run_desc, m_bld_run_script, m_rslv_path, m_run, tmpdir
    ):
        p_tmp_run_dir = tmpdir.ensure_dir("tmp_run_dir")
        m_prepare.return_value = Path(str(p_tmp_run_dir))
        p_results_dir = tmpdir.ensure_dir("results_dir")
        submit_job_msg = mohid_cmd.run.run(
            Path("mohid.yaml"), Path(str(p_results_dir)), no_submit=True
        )
        m_prepare.assert_called_once_with(Path("mohid.yaml"), "")
        m_ld_run_desc.assert_called_once_with(Path("mohid.yaml"))
        m_rslv_path.assert_called_once_with(Path(str(p_results_dir)))
        m_bld_run_script.assert_called_once_with(
            m_ld_run_desc(), Path("mohid.yaml"), m_rslv_path(), m_prepare()
        )
        m_rslv_path().mkdir.assert_called_once_with(parents=True, exist_ok=True)
        assert submit_job_msg is None
        assert not m_run.called


class TestBuildRunScript:
    """Unit test for _build_run_script() function.
    """

    def test_build_run_script(self, run_desc, tmpdir):
        p_mohid_repo = tmpdir.ensure_dir(run_desc["paths"]["mohid repo"])
        p_mohid_exe = p_mohid_repo.ensure("Solutions/linux/bin/MohidWater.exe")
        p_partic_data = tmpdir.ensure_dir(run_desc["run data files"]["PARTIC_DATA"])
        run_desc_patch = {
            "paths": {"mohid repo": str(p_mohid_repo)},
            "run data files": {"PARTIC_DATA": str(p_partic_data)},
        }
        with patch.dict(run_desc, run_desc_patch):
            run_script = mohid_cmd.run._build_run_script(
                run_desc, Path("mohid.yaml"), Path("results_dir"), Path("tmp_run_dir")
            )
        run_id = run_desc["run_id"]
        account = run_desc["account"]
        email = run_desc["email"]
        walltime = run_desc["walltime"]
        expected = textwrap.dedent(
            f"""\
            #!/bin/bash
            
            #SBATCH --job-name={run_id}
            #SBATCH --account={account}
            #SBATCH --mail-user={email}
            #SBATCH --mail-type=ALL
            #SBATCH --cpus-per-task=1
            #SBATCH --mem-per-cpu=14500m
            #SBATCH --time={walltime}
            #SBATCH --output=results_dir/stdout
            #SBATCH --error=results_dir/stderr
            
            if ! test -z $SLURM_CPUS_PER_TASK
            then
              export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
            fi
            
            RUN_ID="{run_id}"
            RUN_DESC="mohid.yaml"
            WORK_DIR="tmp_run_dir"
            RESULTS_DIR="results_dir"
            HDF5_TO_NETCDF4="${{HOME}}/.local/bin/hdf5-to-netcdf4"
            GATHER="${{HOME}}/.local/bin/mohid gather"
            
            module load proj4-fortran/1.0
            module load python/3.7
            module load nco/4.6.6
            
            mkdir -p ${{RESULTS_DIR}}
            cd ${{WORK_DIR}}
            echo "working dir: $(pwd)" >${{RESULTS_DIR}}/stdout
            
            echo "Starting run at $(date)" >>${{RESULTS_DIR}}/stdout
            {str(p_mohid_exe)} >>${{RESULTS_DIR}}/stdout 2>>${{RESULTS_DIR}}/stderr
            MOHID_EXIT_CODE=$?
            echo "Ended run at $(date)" >>${{RESULTS_DIR}}/stdout
            
            TMPDIR="${{SLURM_TMPDIR}}"
            LAGRANGIAN="Lagrangian_DieselFuel_refined_${{RUN_ID}}"
            if test -f ${{WORK_DIR}}/res/${{LAGRANGIAN}}.hdf5
            then
              echo "Results hdf5 to netCDF4 conversion started at $(date)" >>${{RESULTS_DIR}}/stdout
              cp -v ${{WORK_DIR}}/res/${{LAGRANGIAN}}.hdf5 ${{SLURM_TMPDIR}}/ >>${{RESULTS_DIR}}/stdout && \\
              ${{HDF5_TO_NETCDF4}} -v info \\
                ${{SLURM_TMPDIR}}/${{LAGRANGIAN}}.hdf5 \\
                ${{SLURM_TMPDIR}}/${{LAGRANGIAN}}.nc >>${{RESULTS_DIR}}/stdout 2>>${{RESULTS_DIR}}/stderr && \\
              mv -v ${{SLURM_TMPDIR}}/${{LAGRANGIAN}}.nc ${{WORK_DIR}}/ >>${{RESULTS_DIR}}/stdout && \\
              rm -v ${{WORK_DIR}}/res/${{LAGRANGIAN}}.hdf5 >>${{RESULTS_DIR}}/stdout
              echo "Results hdf5 to netCDF4 conversion ended at $(date)" >>${{RESULTS_DIR}}/stdout
            fi
            
            echo "Results gathering started at $(date)" >>${{RESULTS_DIR}}/stdout
            ${{GATHER}} ${{RESULTS_DIR}} --debug >>${{RESULTS_DIR}}/stdout 2>>${{RESULTS_DIR}}/stderr
            echo "Results gathering ended at $(date)" >>${{RESULTS_DIR}}/stdout
            
            chmod -v go+rx ${{RESULTS_DIR}} >>${{RESULTS_DIR}}/stdout
            chmod -v g+rw ${{RESULTS_DIR}}/* >>${{RESULTS_DIR}}/stdout
            chmod -v o+r ${{RESULTS_DIR}}/* >>${{RESULTS_DIR}}/stdout
            
            echo "Deleting run directory" >>${{RESULTS_DIR}}/stdout
            rmdir -v $(pwd) >>${{RESULTS_DIR}}/stdout
            echo "Finished at $(date)" >>${{RESULTS_DIR}}/stdout
            exit ${{MOHID_EXIT_CODE}}
            """
        )
        assert run_script == expected


class TestSbatchDirectives:
    """Unit tests for _sbatch_directives() function.
    """

    def test_email(self, run_desc):
        pass

    def test_account(self, run_desc):
        pass

    def test_sbatch_directives(self, run_desc):
        sbatch_directives = mohid_cmd.run._sbatch_directives(
            run_desc, Path("results_dir")
        )
        expected = textwrap.dedent(
            f"""\
            #SBATCH --job-name={run_desc['run_id']}
            #SBATCH --account={run_desc['account']}
            #SBATCH --mail-user={run_desc['email']}
            #SBATCH --mail-type=ALL
            #SBATCH --cpus-per-task=1
            #SBATCH --mem-per-cpu=14500m
            #SBATCH --time={run_desc['walltime']}
            #SBATCH --output=results_dir/stdout
            #SBATCH --error=results_dir/stderr
            
            if ! test -z $SLURM_CPUS_PER_TASK
            then
              export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
            fi
            """
        )
        assert sbatch_directives == expected


class TestTdToHms:
    """Unit tests for td_to_hms() function.
    """


class TestDefinitions:
    """Unit tests for _definitions() function.
    """

    def test_defns(self, run_desc):
        defns = mohid_cmd.run._definitions(
            run_desc, Path("mohid.yaml"), Path("results_dir"), Path("tmp_run_dir")
        )
        run_id = run_desc["run_id"]
        expected = textwrap.dedent(
            f"""\
            RUN_ID="{run_id}"
            RUN_DESC="mohid.yaml"
            WORK_DIR="tmp_run_dir"
            RESULTS_DIR="results_dir"
            HDF5_TO_NETCDF4="${{HOME}}/.local/bin/hdf5-to-netcdf4"
            GATHER="${{HOME}}/.local/bin/mohid gather"
            """
        )
        assert defns == expected


class TestModules:
    """Unit tests for _modules() function.
    """

    def test_modules(self):
        modules = mohid_cmd.run._modules()
        expected = textwrap.dedent(
            """\
            module load proj4-fortran/1.0
            module load python/3.7
            module load nco/4.6.6
            """
        )
        assert modules == expected


class TestExecute:
    """Unit tests for _execute() function.
    """

    def test_execute(self, run_desc, tmpdir):
        p_mohid_repo = tmpdir.ensure_dir(run_desc["paths"]["mohid repo"])
        p_mohid_exe = p_mohid_repo.ensure("Solutions/linux/bin/MohidWater.exe")
        p_partic_data = tmpdir.ensure_dir(run_desc["run data files"]["PARTIC_DATA"])
        run_desc_patch = {
            "paths": {"mohid repo": str(p_mohid_repo)},
            "run data files": {"PARTIC_DATA": str(p_partic_data)},
        }
        with patch.dict(run_desc, run_desc_patch):
            script = mohid_cmd.run._execute(run_desc)
        expected = textwrap.dedent(
            f"""\
            mkdir -p ${{RESULTS_DIR}}
            cd ${{WORK_DIR}}
            echo "working dir: $(pwd)" >${{RESULTS_DIR}}/stdout
            
            echo "Starting run at $(date)" >>${{RESULTS_DIR}}/stdout
            {str(p_mohid_exe)} >>${{RESULTS_DIR}}/stdout 2>>${{RESULTS_DIR}}/stderr
            MOHID_EXIT_CODE=$?
            echo "Ended run at $(date)" >>${{RESULTS_DIR}}/stdout
            
            TMPDIR="${{SLURM_TMPDIR}}"
            LAGRANGIAN="Lagrangian_DieselFuel_refined_${{RUN_ID}}"
            if test -f ${{WORK_DIR}}/res/${{LAGRANGIAN}}.hdf5
            then
              echo "Results hdf5 to netCDF4 conversion started at $(date)" >>${{RESULTS_DIR}}/stdout
              cp -v ${{WORK_DIR}}/res/${{LAGRANGIAN}}.hdf5 ${{SLURM_TMPDIR}}/ >>${{RESULTS_DIR}}/stdout && \\
              ${{HDF5_TO_NETCDF4}} -v info \\
                ${{SLURM_TMPDIR}}/${{LAGRANGIAN}}.hdf5 \\
                ${{SLURM_TMPDIR}}/${{LAGRANGIAN}}.nc >>${{RESULTS_DIR}}/stdout 2>>${{RESULTS_DIR}}/stderr && \\
              mv -v ${{SLURM_TMPDIR}}/${{LAGRANGIAN}}.nc ${{WORK_DIR}}/ >>${{RESULTS_DIR}}/stdout && \\
              rm -v ${{WORK_DIR}}/res/${{LAGRANGIAN}}.hdf5 >>${{RESULTS_DIR}}/stdout
              echo "Results hdf5 to netCDF4 conversion ended at $(date)" >>${{RESULTS_DIR}}/stdout
            fi
            
            echo "Results gathering started at $(date)" >>${{RESULTS_DIR}}/stdout
            ${{GATHER}} ${{RESULTS_DIR}} --debug >>${{RESULTS_DIR}}/stdout 2>>${{RESULTS_DIR}}/stderr
            echo "Results gathering ended at $(date)" >>${{RESULTS_DIR}}/stdout
            """
        )
        assert script == expected


class TestFixPermissions:
    """Unit tests for _fix_permissions() function.
    """

    def test_fix_permissions(self):
        script = mohid_cmd.run._fix_permissions()
        expected = textwrap.dedent(
            """\
            chmod -v go+rx ${RESULTS_DIR} >>${RESULTS_DIR}/stdout
            chmod -v g+rw ${RESULTS_DIR}/* >>${RESULTS_DIR}/stdout
            chmod -v o+r ${RESULTS_DIR}/* >>${RESULTS_DIR}/stdout
            """
        )
        assert script == expected


class TestCleanup:
    """Unit tests for _cleanup() function.
    """

    def test_cleanup(self):
        script = mohid_cmd.run._cleanup()
        expected = textwrap.dedent(
            """\
            echo "Deleting run directory" >>${RESULTS_DIR}/stdout
            rmdir -v $(pwd) >>${RESULTS_DIR}/stdout
            echo "Finished at $(date)" >>${RESULTS_DIR}/stdout
            exit ${MOHID_EXIT_CODE}
            """
        )
        assert script == expected
