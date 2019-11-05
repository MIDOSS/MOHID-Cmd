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
import textwrap
from pathlib import Path
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock, patch, call

import pytest
import yaml

import mohid_cmd.run


@pytest.fixture
def run_cmd():
    return mohid_cmd.run.Run(Mock(spec=True), [])


@pytest.fixture()
def run_desc(tmpdir):
    p_run_desc = tmpdir.join("mohid.yaml")
    p_run_desc.write(
        textwrap.dedent(
            """\
            run_id: MarathassaConstTS
            email: you@example.com
            account: def-allen
            walltime: "1:30:00"

            paths:
              mohid repo: MIDOSS-MOHID/

            run data files:
              PARTIC_DATA: MIDOSS-MOHID-config/MarathassaConstTS/Lagrangian_DieselFuel_refined.dat
            """
        )
    )
    with open(str(p_run_desc), "rt") as f:
        run_desc = yaml.safe_load(f)
    return run_desc


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

    def test_no_submit_argument(self, run_cmd):
        parser = run_cmd.get_parser("mohid run")
        assert parser._actions[3].dest == "no_submit"
        assert parser._actions[3].option_strings == ["--no-submit"]
        assert parser._actions[3].const is True
        assert parser._actions[3].default is False
        assert parser._actions[3].help

    def test_quiet_argument(self, run_cmd):
        parser = run_cmd.get_parser("mohid run")
        assert parser._actions[4].dest == "quiet"
        assert parser._actions[4].option_strings == ["-q", "--quiet"]
        assert parser._actions[4].const is True
        assert parser._actions[4].default is False
        assert parser._actions[4].help

    def test_parsed_args_defaults(self, run_cmd):
        parser = run_cmd.get_parser("mohid run")
        parsed_args = parser.parse_args(["foo.yaml", "results/foo/"])
        assert parsed_args.desc_file == Path("foo.yaml")
        assert parsed_args.results_dir == Path("results/foo/")
        assert not parsed_args.no_submit
        assert not parsed_args.quiet

    @pytest.mark.parametrize("flag", ["-q", "--quiet"])
    def test_parsed_args_quiet_options(self, flag, run_cmd):
        parser = run_cmd.get_parser("mohid run")
        parsed_args = parser.parse_args(["foo.yaml", "results/foo/", flag])
        assert parsed_args.quiet is True

    def test_parsed_args_no_submit_option(self, run_cmd):
        parser = run_cmd.get_parser("mohid run")
        parsed_args = parser.parse_args(["foo.yaml", "results/foo/", "--no-submit"])
        assert parsed_args.no_submit is True


@patch("mohid_cmd.run.logger", autospec=True)
class TestTakeAction:
    """Unit tests for `mohid run` sub-command take_action() method.
    """

    @patch("mohid_cmd.run.run", return_value="submit job msg", autospec=True)
    def test_take_action(self, m_run, m_logger, run_cmd):
        parsed_args = SimpleNamespace(
            desc_file=Path("desc file"),
            results_dir=Path("results dir"),
            no_submit=False,
            quiet=False,
        )
        run_cmd.take_action(parsed_args)
        m_run.assert_called_once_with(
            Path("desc file"), Path("results dir"), no_submit=False, quiet=False
        )
        m_logger.info.assert_called_once_with("submit job msg")

    @patch("mohid_cmd.run.run", return_value="submit job msg", autospec=True)
    def test_take_action_quiet(self, m_run, m_logger, run_cmd):
        parsed_args = SimpleNamespace(
            desc_file=Path("desc file"),
            results_dir=Path("results dir"),
            no_submit=False,
            quiet=True,
        )
        run_cmd.take_action(parsed_args)
        assert not m_logger.info.called

    @patch("mohid_cmd.run.run", return_value=None, autospec=True)
    def test_take_action_no_submit(self, m_run, m_logger, run_cmd):
        parsed_args = SimpleNamespace(
            desc_file=Path("desc file"),
            results_dir=Path("results dir"),
            no_submit=True,
            quiet=True,
        )
        run_cmd.take_action(parsed_args)
        assert not m_logger.info.called


@patch("mohid_cmd.run.subprocess.run", autospec=True)
@patch("mohid_cmd.run.nemo_cmd.resolved_path", spec=True)
@patch("mohid_cmd.run._build_run_script", return_value="script", autospec=True)
@patch("mohid_cmd.run.nemo_cmd.prepare.load_run_desc", spec=True)
@patch("mohid_cmd.run.api.prepare", spec=True)
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
        m_prepare.assert_called_once_with(Path("mohid.yaml"))
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
        m_prepare.assert_called_once_with(Path("mohid.yaml"))
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
            #SBATCH --mem-per-cpu=20000m
            #SBATCH --time={walltime}
            #SBATCH --output=results_dir/stdout
            #SBATCH --error=results_dir/stderr
            
            export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
            
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
            echo "working dir: $(pwd)"
            
            echo "Starting run at $(date)"
            {str(p_mohid_exe)}
            MOHID_EXIT_CODE=$?
            echo "Ended run at $(date)"
            
            echo "Results hdf5 to netCDF4 conversion started at $(date)"
            TMPDIR="${{SLURM_TMPDIR}}"
            cp ${{WORK_DIR}}/res/Lagrangian_DieselFuel_refined_${{RUN_ID}}.hdf5 ${{SLURM_TMPDIR}}/
            ${{HDF5_TO_NETCDF4}} -v info \\
              ${{SLURM_TMPDIR}}/Lagrangian_DieselFuel_refined_${{RUN_ID}}.hdf5 \\
              ${{SLURM_TMPDIR}}/Lagrangian_DieselFuel_refined_${{RUN_ID}}.nc
            cp ${{SLURM_TMPDIR}}/Lagrangian_DieselFuel_refined_${{RUN_ID}}.nc ${{WORK_DIR}}/
            echo "Results hdf5 to netCDF4 conversion ended at $(date)"
            
            echo "Results gathering started at $(date)"
            ${{GATHER}} ${{RESULTS_DIR}} --debug
            echo "Results gathering ended at $(date)"
            
            chmod go+rx ${{RESULTS_DIR}}
            chmod g+rw ${{RESULTS_DIR}}/*
            chmod o+r ${{RESULTS_DIR}}/*
            
            echo "Deleting run directory"
            rmdir $(pwd)
            echo "Finished at $(date)"
            exit ${{MPIRUN_EXIT_CODE}}
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
            #SBATCH --mem-per-cpu=20000m
            #SBATCH --time={run_desc['walltime']}
            #SBATCH --output=results_dir/stdout
            #SBATCH --error=results_dir/stderr
            
            export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
            """
        )
        assert sbatch_directives == expected


class TestTdToHms:
    """Unit tests for _td_to_hms() function.
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
            echo "working dir: $(pwd)"
            
            echo "Starting run at $(date)"
            {str(p_mohid_exe)}
            MOHID_EXIT_CODE=$?
            echo "Ended run at $(date)"
            
            echo "Results hdf5 to netCDF4 conversion started at $(date)"
            TMPDIR="${{SLURM_TMPDIR}}"
            cp ${{WORK_DIR}}/res/Lagrangian_DieselFuel_refined_${{RUN_ID}}.hdf5 ${{SLURM_TMPDIR}}/
            ${{HDF5_TO_NETCDF4}} -v info \\
              ${{SLURM_TMPDIR}}/Lagrangian_DieselFuel_refined_${{RUN_ID}}.hdf5 \\
              ${{SLURM_TMPDIR}}/Lagrangian_DieselFuel_refined_${{RUN_ID}}.nc
            cp ${{SLURM_TMPDIR}}/Lagrangian_DieselFuel_refined_${{RUN_ID}}.nc ${{WORK_DIR}}/
            echo "Results hdf5 to netCDF4 conversion ended at $(date)"
            
            echo "Results gathering started at $(date)"
            ${{GATHER}} ${{RESULTS_DIR}} --debug
            echo "Results gathering ended at $(date)"
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
            chmod go+rx ${RESULTS_DIR}
            chmod g+rw ${RESULTS_DIR}/*
            chmod o+r ${RESULTS_DIR}/*
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
            echo "Deleting run directory"
            rmdir $(pwd)
            echo "Finished at $(date)"
            exit ${MPIRUN_EXIT_CODE}
            """
        )
        assert script == expected
