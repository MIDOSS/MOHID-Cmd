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
    runs_dir.mkdir(parents=True)

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
              
            mohid command: $HOME/.local/bin/mohid
            """
        )
    )
    with run_desc_file.open("rt") as fp:
        run_desc = yaml.safe_load(fp)
    return run_desc


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
        self, monte_carlo_cmd, glost_run_desc, mock_subprocess_run, caplog, tmp_path
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
        self, monte_carlo_cmd, glost_run_desc, mock_subprocess_run, caplog, tmp_path
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
    """Unit tests for mohid.monte-carlo.monte_carlo() function.
    """

    def test_no_submit(self, mock_subprocess_run, glost_run_desc, tmp_path):
        submit_job_msg = mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        assert submit_job_msg is None

    def test_submit(self, mock_subprocess_run, glost_run_desc, tmp_path):
        submit_job_msg = mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml",
            tmp_path / "AKNS_spatial.csv",
            no_submit=False,
        )
        assert submit_job_msg == "Submitted batch job 12345678"


class TestGlostJobDir:
    """Integration tests for GLOST job directory generated by `mohid monte-carlo` sub-command.
    """

    @staticmethod
    @pytest.fixture
    def mock_arrow_now(monkeypatch):
        def mock_arrow_now():
            return arrow.get("2019-11-24T170743")

        monkeypatch.setattr(mohid_cmd.monte_carlo.arrow, "now", mock_arrow_now)

    def test_job_dir_created(self, mock_arrow_now, glost_run_desc, tmp_path):
        mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        runs_dir = glost_run_desc["paths"]["runs directory"]
        job_id = glost_run_desc["job id"]
        assert (Path(runs_dir) / f"{job_id}_2019-11-24T170743").is_dir()

    def test_forcing_yaml_dir_created(self, mock_arrow_now, glost_run_desc, tmp_path):
        mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        runs_dir = glost_run_desc["paths"]["runs directory"]
        job_id = glost_run_desc["job id"]
        assert (
            Path(runs_dir) / f"{job_id}_2019-11-24T170743" / "forcing-yaml"
        ).is_dir()

    def test_mohid_yaml_dir_created(self, mock_arrow_now, glost_run_desc, tmp_path):
        mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        runs_dir = glost_run_desc["paths"]["runs directory"]
        job_id = glost_run_desc["job id"]
        assert (Path(runs_dir) / f"{job_id}_2019-11-24T170743" / "mohid-yaml").is_dir()

    def test_results_dir_created(self, mock_arrow_now, glost_run_desc, tmp_path):
        mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        runs_dir = glost_run_desc["paths"]["runs directory"]
        job_id = glost_run_desc["job id"]
        assert (Path(runs_dir) / f"{job_id}_2019-11-24T170743" / "results").is_dir()

    def test_glost_tasks_file_created(self, mock_arrow_now, glost_run_desc, tmp_path):
        mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        runs_dir = glost_run_desc["paths"]["runs directory"]
        job_id = glost_run_desc["job id"]
        job_dir = Path(runs_dir) / f"{job_id}_2019-11-24T170743"
        assert (job_dir / "glost-tasks.txt").is_file()

    def test_glost_tasks_file_contents(self, mock_arrow_now, glost_run_desc, tmp_path):
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

    def test_glost_job_script_created(self, mock_arrow_now, glost_run_desc, tmp_path):
        mohid_cmd.monte_carlo.monte_carlo(
            tmp_path / "monte-carlo.yaml", tmp_path / "AKNS_spatial.csv", no_submit=True
        )
        runs_dir = glost_run_desc["paths"]["runs directory"]
        job_id = glost_run_desc["job id"]
        job_dir = Path(runs_dir) / f"{job_id}_2019-11-24T170743"
        assert (job_dir / "glost-job.sh").is_file()

    def test_glost_job_script_contents(self, mock_arrow_now, glost_run_desc, tmp_path):
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
