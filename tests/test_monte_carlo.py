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
import logging
from pathlib import Path
import textwrap
from types import SimpleNamespace

import arrow
import attr
import jinja2
import numpy
import pandas
import pytest
import yaml

import mohid_cmd.main
import mohid_cmd.monte_carlo


@pytest.fixture
def monte_carlo_cmd():
    return mohid_cmd.monte_carlo.MonteCarlo(mohid_cmd.main.MohidApp, [])


@pytest.fixture
def glost_run_desc(tmp_path):
    runs_dir = tmp_path / "monte-carlo"
    runs_dir.mkdir()

    code_repo = tmp_path / "MIDOSS-MOHID-CODE"
    code_repo.mkdir()
    config_repo = tmp_path / "MIDOSS-MOHID-config"
    config_repo.mkdir()
    grid_repo = tmp_path / "MIDOSS-MOHID-grid"
    grid_repo.mkdir()
    mohid_cmd_repo = tmp_path / "MOHID-Cmd"
    mohid_cmd_repo.mkdir()
    nemo_cmd_repo = tmp_path / "NEMO-Cmd"
    nemo_cmd_repo.mkdir()
    moad_tools_repo = tmp_path / "moad_tools"
    moad_tools_repo.mkdir()

    mohid_config_dir = config_repo / "monte-carlo"
    mohid_config_dir.mkdir()

    run_desc_file = tmp_path / "monte-carlo.yaml"
    run_desc_file.write_text(
        textwrap.dedent(
            f"""\
            job id: AKNS-spatial
            account: rrg-allen
            email: dlatorne@example.com
            nodes: 1
            tasks per node: 3
            runs per glost job: 2
            mem per cpu: 14000M
            run walltime: 2:00:00   

            paths:
              runs directory: {runs_dir}
              mohid config: {mohid_config_dir}
              
            mohid command: $HOME/.local/bin/mohid
            
            vcs revisions:
              hg:
                - {code_repo}
                - {config_repo}
                - {grid_repo}
                - {mohid_cmd_repo}
                - {nemo_cmd_repo}
                - {moad_tools_repo}
            """
        )
    )
    with run_desc_file.open("rt") as fp:
        run_desc = yaml.safe_load(fp)
    return run_desc


@pytest.fixture
def mock_get_runs_info(monkeypatch):
    def mock_get_runs_info(*args):
        pass

    monkeypatch.setattr(mohid_cmd.monte_carlo, "_get_runs_info", mock_get_runs_info)


@pytest.fixture
def mock_render_mohid_run_yamls(monkeypatch):
    def mock_render_mohid_run_yamls(*args):
        pass

    monkeypatch.setattr(
        mohid_cmd.monte_carlo, "_render_mohid_run_yamls", mock_render_mohid_run_yamls
    )


@pytest.fixture
def mock_record_vcs_revisions(monkeypatch):
    def mock_record_vcs_revisions(*args):
        pass

    monkeypatch.setattr(
        mohid_cmd.monte_carlo.nemo_cmd.prepare,
        "record_vcs_revisions",
        mock_record_vcs_revisions,
    )


@pytest.fixture
def mock_subprocess_run(monkeypatch):
    def mock_subprocess_run(*args, **kwargs):
        @attr.s
        class CompletedProcess:
            stdout = attr.ib(default="Submitted batch job 12345678")

        return CompletedProcess()

    monkeypatch.setattr(mohid_cmd.monte_carlo.subprocess, "run", mock_subprocess_run)


class TestParser:
    """Unit tests for `mohid monte-carlo` sub-command command-line parser.
    """

    def test_get_parser(self, monte_carlo_cmd):
        parser = monte_carlo_cmd.get_parser("mohid monte-carlo")
        assert parser.prog == "mohid monte-carlo"

    def test_cmd_description(self, monte_carlo_cmd):
        parser = monte_carlo_cmd.get_parser("mohid monte-carlo")
        assert parser.description.strip().startswith(
            "Prepare for and execute a collection of Monte Carlo runs"
        )

    def test_desc_file_argument(self, monte_carlo_cmd):
        parser = monte_carlo_cmd.get_parser("mohid monte-carlo")
        assert parser._actions[1].dest == "desc_file"
        assert parser._actions[1].metavar == "DESC_FILE"
        assert parser._actions[1].type == Path
        assert parser._actions[1].help

    def test_csv_file_argument(self, monte_carlo_cmd):
        parser = monte_carlo_cmd.get_parser("mohid monte-carlo")
        assert parser._actions[2].dest == "csv_file"
        assert parser._actions[2].metavar == "CSV_FILE"
        assert parser._actions[2].type == Path
        assert parser._actions[2].help

    def test_no_submit_option(self, monte_carlo_cmd):
        parser = monte_carlo_cmd.get_parser("mohid monte-carlo")
        assert parser._actions[3].dest == "no_submit"
        assert parser._actions[3].option_strings == ["--no-submit"]
        assert parser._actions[3].const is True
        assert parser._actions[3].default is False
        assert parser._actions[3].help

    def test_parsed_args(self, monte_carlo_cmd):
        parser = monte_carlo_cmd.get_parser("mohid monte-carlo")
        parsed_args = parser.parse_args(
            [
                "config/monte-carlo/monte-carlo.yaml",
                "config/monte-carlo/AKNS_spatial.csv",
            ]
        )
        assert parsed_args.desc_file == Path("config/monte-carlo/monte-carlo.yaml")
        assert parsed_args.csv_file == Path("config/monte-carlo/AKNS_spatial.csv")

    def test_parsed_args_option_defaults(self, monte_carlo_cmd):
        parser = monte_carlo_cmd.get_parser("mohid monte-carlo")
        parsed_args = parser.parse_args(
            [
                "config/monte-carlo/monte-carlo.yaml",
                "config/monte-carlo/AKNS_spatial.csv",
            ]
        )
        assert parsed_args.no_submit is False


class TestTakeAction:
    """Unit tests for `mohid monte-carlo` sub-command take_action() method.
    """

    def test_take_action(
        self,
        mock_get_runs_info,
        mock_render_mohid_run_yamls,
        mock_record_vcs_revisions,
        monte_carlo_cmd,
        glost_run_desc,
        mock_subprocess_run,
        caplog,
        tmp_path,
    ):
        desc_file = tmp_path / "monte-carlo.yaml"
        csv_file = tmp_path / "AKNS_spatial.csv"
        parsed_args = SimpleNamespace(
            desc_file=desc_file, csv_file=csv_file, no_submit=False
        )
        caplog.set_level(logging.INFO)
        monte_carlo_cmd.take_action(parsed_args)
        assert caplog.records[0].levelname == "INFO"
        assert caplog.messages[0] == "Submitted batch job 12345678"

    def test_take_action_no_submit(
        self,
        mock_get_runs_info,
        mock_render_mohid_run_yamls,
        mock_record_vcs_revisions,
        monte_carlo_cmd,
        glost_run_desc,
        mock_subprocess_run,
        caplog,
        tmp_path,
    ):
        desc_file = tmp_path / "monte-carlo.yaml"
        csv_file = tmp_path / "AKNS_spatial.csv"
        parsed_args = SimpleNamespace(
            desc_file=desc_file, csv_file=csv_file, no_submit=True
        )
        caplog.set_level(logging.INFO)
        monte_carlo_cmd.take_action(parsed_args)
        assert not caplog.records


class TestMonteCarlo:
    """Unit tests for monte_carlo() function.
    """

    def test_no_submit(
        self,
        mock_get_runs_info,
        mock_render_mohid_run_yamls,
        mock_record_vcs_revisions,
        mock_subprocess_run,
        glost_run_desc,
        tmp_path,
    ):
        submit_job_msg = mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        assert submit_job_msg is None

    def test_submit(
        self,
        mock_get_runs_info,
        mock_render_mohid_run_yamls,
        mock_record_vcs_revisions,
        mock_subprocess_run,
        glost_run_desc,
        tmp_path,
    ):
        submit_job_msg = mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml",
            tmp_path / "AKNS_spatial.csv",
            no_submit=False,
        )
        assert submit_job_msg == "Submitted batch job 12345678"


class TestRenderMohidRunYamls:
    """Unit test for _render_mohid_run_yamls() function.
    """

    def test_render_mohid_run_yamls(self, glost_run_desc, monkeypatch):
        @attr.s
        class MockJinja2Environment:
            loader = attr.ib()

            def get_template(self, name):
                return jinja2.Template(
                    textwrap.dedent(
                        """\
                    run_id: {{ job_id }}-{{ run_number }}

                    forcing:
                      winds.hdf5: /scratch/dlatorne/MIDOSS/forcing/SOG_{{ start_ddmmmyy }}_{{ end_ddmmmyy }}/winds.hdf5
                      currents.hdf5: /scratch/dlatorne/MIDOSS/forcing/SOG_{{ start_ddmmmyy }}_{{ end_ddmmmyy }}/currents.hdf5
                      water_levels.hdf5: /scratch/dlatorne/MIDOSS/forcing/SOG_{{ start_ddmmmyy }}_{{ end_ddmmmyy }}/t.hdf5
                      temperature.hdf5: /scratch/dlatorne/MIDOSS/forcing/SOG_{{ start_ddmmmyy }}_{{ end_ddmmmyy }}/t.hdf5
                      salinity.hdf5: /scratch/dlatorne/MIDOSS/forcing/SOG_{{ start_ddmmmyy }}_{{ end_ddmmmyy }}/t.hdf5
                      ww3.hdf5: /scratch/dlatorne/MIDOSS/forcing/SOG_{{ start_ddmmmyy }}_{{ end_ddmmmyy }}/waves_stokes.hdf5
                      e3t.hdf5: /scratch/dlatorne/MIDOSS/forcing/SOG_{{ start_ddmmmyy }}_{{ end_ddmmmyy }}/e3t.hdf5

                    run data files:
                      IN_MODEL: {{ job_dir }}/mohid-yaml/Model-{{ run_number }}.dat
                      PARTIC_DATA: {{ job_dir }}/mohid-yaml/{{ Lagrangian_template }}-{{ run_number }}.dat
                    """
                    )
                )

        job_id = glost_run_desc["job id"]
        runs_dir = glost_run_desc["paths"]["runs directory"]
        job_dir = Path(runs_dir) / f"{job_id}_2019-12-04T180843"
        mohid_yaml_dir = job_dir / "mohid-yaml"
        mohid_yaml_dir.mkdir(parents=True)
        runs = pandas.DataFrame(
            {
                "spill_date_hour": pandas.Timestamp("2017-06-15 02:00"),
                "run_days": numpy.array([7], dtype=numpy.int64),
                "Lagrangian_template": "Lagrangian_AKNS_crude.dat",
            }
        )

        mohid_cmd.monte_carlo._render_mohid_run_yamls(
            job_id, job_dir, runs, MockJinja2Environment("loader")
        )
        with (mohid_yaml_dir / f"{job_id}-0.yaml").open("rt") as fp:
            run_desc = yaml.safe_load(fp)
        assert run_desc["run_id"] == f"{job_id}-0"
        assert (
            run_desc["forcing"]["winds.hdf5"]
            == "/scratch/dlatorne/MIDOSS/forcing/SOG_15jun17_22jun17/winds.hdf5"
        )
        assert (
            run_desc["forcing"]["currents.hdf5"]
            == "/scratch/dlatorne/MIDOSS/forcing/SOG_15jun17_22jun17/currents.hdf5"
        )
        assert (
            run_desc["forcing"]["water_levels.hdf5"]
            == "/scratch/dlatorne/MIDOSS/forcing/SOG_15jun17_22jun17/t.hdf5"
        )
        assert (
            run_desc["forcing"]["temperature.hdf5"]
            == "/scratch/dlatorne/MIDOSS/forcing/SOG_15jun17_22jun17/t.hdf5"
        )
        assert (
            run_desc["forcing"]["salinity.hdf5"]
            == "/scratch/dlatorne/MIDOSS/forcing/SOG_15jun17_22jun17/t.hdf5"
        )
        assert (
            run_desc["forcing"]["ww3.hdf5"]
            == "/scratch/dlatorne/MIDOSS/forcing/SOG_15jun17_22jun17/waves_stokes.hdf5"
        )
        assert (
            run_desc["forcing"]["e3t.hdf5"]
            == "/scratch/dlatorne/MIDOSS/forcing/SOG_15jun17_22jun17/e3t.hdf5"
        )
        assert (
            run_desc["run data files"]["IN_MODEL"]
            == f"{job_dir}/mohid-yaml/Model-0.dat"
        )
        assert (
            run_desc["run data files"]["PARTIC_DATA"]
            == f"{job_dir}/mohid-yaml/Lagrangian_AKNS_crude-0.dat"
        )


class TestGlostJobDir:
    """Integration tests for GLOST job directory generated by `mohid monte-carlo` sub-command.
    """

    @staticmethod
    @pytest.fixture
    def mock_arrow_now(monkeypatch):
        def mock_arrow_now():
            return arrow.get("2019-11-24T170743")

        monkeypatch.setattr(mohid_cmd.monte_carlo.arrow, "now", mock_arrow_now)

    @staticmethod
    @pytest.fixture
    def mock_hg_repo(monkeypatch):
        @attr.s
        class MockHgRevision:
            rev = attr.ib(default=b"43")
            node = attr.ib(default=b"f7d21a1dfad4")
            tags = attr.ib(default=b"tip")
            author = attr.ib(default=b"Doug Latornell <dlatornell@example.com>")
            date = attr.ib(default=arrow.get("2019-10-25 19:30:43").naive)
            files = attr.ib(default=[b"foo/bar.py", b"foo/baz.py"])
            desc = attr.ib(
                default=b"Refactor the Frobnitzicator class\n\nImprove disambiguation\n"
            )

        @attr.s
        class MockHgRepo:
            repo_path = attr.ib()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

            def parents(self):
                return [MockHgRevision()]

            def status(
                self,
                rev=None,
                change=None,
                modified=None,
                added=None,
                removed=None,
                deleted=None,
                copies=None,
            ):
                return []

        monkeypatch.setattr(
            mohid_cmd.monte_carlo.nemo_cmd.prepare.hglib, "open", MockHgRepo
        )

    def test_job_dir_created(
        self,
        mock_arrow_now,
        mock_get_runs_info,
        mock_render_mohid_run_yamls,
        mock_hg_repo,
        glost_run_desc,
        tmp_path,
    ):
        mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        runs_dir = glost_run_desc["paths"]["runs directory"]
        job_id = glost_run_desc["job id"]
        assert (Path(runs_dir) / f"{job_id}_2019-11-24T170743").is_dir()

    def test_forcing_yaml_dir_created(
        self,
        mock_arrow_now,
        mock_get_runs_info,
        mock_render_mohid_run_yamls,
        mock_hg_repo,
        glost_run_desc,
        tmp_path,
    ):
        mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        runs_dir = glost_run_desc["paths"]["runs directory"]
        job_id = glost_run_desc["job id"]
        assert (
            Path(runs_dir) / f"{job_id}_2019-11-24T170743" / "forcing-yaml"
        ).is_dir()

    def test_mohid_yaml_dir_created(
        self,
        mock_arrow_now,
        mock_get_runs_info,
        mock_render_mohid_run_yamls,
        mock_hg_repo,
        glost_run_desc,
        tmp_path,
    ):
        mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        runs_dir = glost_run_desc["paths"]["runs directory"]
        job_id = glost_run_desc["job id"]
        assert (Path(runs_dir) / f"{job_id}_2019-11-24T170743" / "mohid-yaml").is_dir()

    def test_mohid_yaml_files_created(
        self, mock_arrow_now, mock_hg_repo, glost_run_desc, tmp_path, monkeypatch
    ):
        n_runs = 2

        def mock_get_runs_info(*args):
            runs = pandas.DataFrame(
                {
                    "spill_date_hour": pandas.Timestamp("2017-06-15 02:00"),
                    "run_days": numpy.array([7] * n_runs, dtype=numpy.int64),
                    "Lagrangian_template": "Lagrangian_AKNS_crude.dat",
                }
            )
            return runs

        monkeypatch.setattr(mohid_cmd.monte_carlo, "_get_runs_info", mock_get_runs_info)

        tmpl_dir = Path(glost_run_desc["paths"]["mohid config"], "templates")
        tmpl_dir.mkdir()
        (tmpl_dir / "mohid-run.yaml").write_text("")

        mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        runs_dir = glost_run_desc["paths"]["runs directory"]
        job_id = glost_run_desc["job id"]
        mohid_yaml_dir = Path(runs_dir) / f"{job_id}_2019-11-24T170743" / "mohid-yaml"
        for i in range(n_runs):
            assert (mohid_yaml_dir / f"{job_id}-{i}.yaml").exists()

    def test_results_dir_created(
        self,
        mock_arrow_now,
        mock_get_runs_info,
        mock_render_mohid_run_yamls,
        mock_hg_repo,
        glost_run_desc,
        tmp_path,
    ):
        mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        runs_dir = glost_run_desc["paths"]["runs directory"]
        job_id = glost_run_desc["job id"]
        assert (Path(runs_dir) / f"{job_id}_2019-11-24T170743" / "results").is_dir()

    def test_glost_tasks_file_created(
        self,
        mock_arrow_now,
        mock_get_runs_info,
        mock_render_mohid_run_yamls,
        mock_hg_repo,
        glost_run_desc,
        tmp_path,
    ):
        mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        runs_dir = glost_run_desc["paths"]["runs directory"]
        job_id = glost_run_desc["job id"]
        job_dir = Path(runs_dir) / f"{job_id}_2019-11-24T170743"
        assert (job_dir / "glost-tasks.txt").is_file()

    def test_glost_tasks_file_contents(
        self,
        mock_arrow_now,
        mock_get_runs_info,
        mock_render_mohid_run_yamls,
        mock_hg_repo,
        glost_run_desc,
        tmp_path,
    ):
        mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        runs_dir = glost_run_desc["paths"]["runs directory"]
        job_id = glost_run_desc["job id"]
        job_dir = Path(runs_dir) / f"{job_id}_2019-11-24T170743"
        # ignore newline at end of file
        glost_tasks = (job_dir / "glost-tasks.txt").read_text().splitlines()[:-1]
        expected = [
            # 2 GLOST tasks
            f"$HOME/.local/bin/mohid run "
            f"--no-submit "
            f"--tmp-run-dir $MONTE_CARLO/{job_id}-0 "
            f"$MONTE_CARLO/mohid-yaml/{job_id}-0.yaml "
            f"$MONTE_CARLO/results/{job_id}-0/ "
            f"&& "
            f"bash $MONTE_CARLO/{job_id}-0/MOHID.sh",
            #
            f"$HOME/.local/bin/mohid run "
            f"--no-submit "
            f"--tmp-run-dir $MONTE_CARLO/{job_id}-1 "
            f"$MONTE_CARLO/mohid-yaml/{job_id}-1.yaml "
            f"$MONTE_CARLO/results/{job_id}-1/ "
            f"&& "
            f"bash $MONTE_CARLO/{job_id}-1/MOHID.sh",
        ]
        assert glost_tasks == expected

    def test_glost_job_script_created(
        self,
        mock_arrow_now,
        mock_get_runs_info,
        mock_render_mohid_run_yamls,
        mock_hg_repo,
        glost_run_desc,
        tmp_path,
    ):
        mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        runs_dir = glost_run_desc["paths"]["runs directory"]
        job_id = glost_run_desc["job id"]
        job_dir = Path(runs_dir) / f"{job_id}_2019-11-24T170743"
        assert (job_dir / "glost-job.sh").is_file()

    def test_glost_job_script_contents(
        self,
        mock_arrow_now,
        mock_get_runs_info,
        mock_render_mohid_run_yamls,
        mock_hg_repo,
        glost_run_desc,
        tmp_path,
    ):
        mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        runs_dir = glost_run_desc["paths"]["runs directory"]
        job_id = glost_run_desc["job id"]
        job_dir = Path(runs_dir) / f"{job_id}_2019-11-24T170743"
        glost_script = (job_dir / "glost-job.sh").read_text().splitlines()
        expected = textwrap.dedent(
            f"""\
            #!/bin/bash
            
            #SBATCH --job-name={job_id}
            #SBATCH --account={glost_run_desc["account"]}
            #SBATCH --mail-user={glost_run_desc["email"]}
            #SBATCH --mail-type=ALL
            #SBATCH --nodes={glost_run_desc["nodes"]}
            #SBATCH --ntasks-per-node={glost_run_desc["tasks per node"]}
            #SBATCH --mem-per-cpu={glost_run_desc["mem per cpu"]}
            #SBATCH --time=2:00:00
            #SBATCH --output={job_dir}/glost-job.stdout
            #SBATCH --error={job_dir}/glost-job.stderr
            
            module load glost/0.3.1
            module load python/3.7
            module load proj4-fortran/1.0
            module load nco/4.6.6
            
            export MONTE_CARLO/={job_dir}
            
            echo "Starting glost at $(date)"
            srun glost_launch {job_dir}/glost-tasks.txt
            echo "Ended glost at $(date)"
            """
        ).splitlines()
        assert glost_script == expected

    def test_vcs_rev_record_files_created(
        self,
        mock_arrow_now,
        mock_get_runs_info,
        mock_render_mohid_run_yamls,
        mock_hg_repo,
        glost_run_desc,
        tmp_path,
    ):
        mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        runs_dir = glost_run_desc["paths"]["runs directory"]
        job_id = glost_run_desc["job id"]
        job_dir = Path(runs_dir) / f"{job_id}_2019-11-24T170743"
        assert (job_dir / "MIDOSS-MOHID-CODE_rev.txt").is_file()
        assert (job_dir / "MIDOSS-MOHID-config_rev.txt").is_file()
        assert (job_dir / "MIDOSS-MOHID-grid_rev.txt").is_file()
        assert (job_dir / "MOHID-Cmd_rev.txt").is_file()
        assert (job_dir / "NEMO-Cmd_rev.txt").is_file()
        assert (job_dir / "moad_tools_rev.txt").is_file()
