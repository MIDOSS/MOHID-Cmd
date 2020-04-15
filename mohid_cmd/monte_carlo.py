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
"""MOHID-Cmd command plug-in for monte-carlo sub-command.

Prepare for and execute a collection of Monte Carlo runs of the MIDOSS-MOHID model.
"""
import datetime
import logging
import os
import shlex
import shutil
import subprocess
from pathlib import Path

import arrow
import cliff.command
import cookiecutter.main
import jinja2
import nemo_cmd.prepare
import pandas

import mohid_cmd.run

logger = logging.getLogger(__name__)


class MonteCarlo(cliff.command.Command):
    """Prepare for and execute a collection of Monte Carlo runs of the MIDOSS-MOHID model.
    """

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.description = """
            Prepare for and execute a collection of Monte Carlo runs of the MIDOSS-MOHID model
            as a glost job.
            
            The glost job is described in DESC_FILE.
            The parameters of the MIDOSS-MOHID runs are defined in CSV_FILE.
            The results directories from the runs are gathered in RESULTS_DIR.
            
            If RESULTS_DIR does ont exist, it will be created.
        """
        parser.add_argument(
            "desc_file",
            metavar="DESC_FILE",
            type=Path,
            help="glost job description YAML file",
        )
        parser.add_argument(
            "csv_file",
            metavar="CSV_FILE",
            type=Path,
            help="MIDOSS-MOHID run parameters CSV file",
        )
        parser.add_argument(
            "--no-submit",
            dest="no_submit",
            action="store_true",
            help="""
            Prepare the directories of forcing YAML files,
            MIDOSS-MOHID run description YAML files,
            top level results directory, 
            and the bash script to execute the glost job, 
            but don't submit the glost job to the queue.
            This is useful during development runs when you want to hack on 
            the bash script and/or use the same setup directories 
            more than once.
            """,
        )
        return parser

    def take_action(self, parsed_args):
        """Execute the `mohid monte-carlo` sub-coomand.

        The message generated upon submission of the glost run to the queue
        manager is logged to the console.

        :param parsed_args: Arguments and options parsed from the command-line.
        :type parsed_args: :class:`argparse.Namespace` instance
        """
        submit_job_msg = monte_carlo(
            parsed_args.desc_file, parsed_args.csv_file, no_submit=parsed_args.no_submit
        )
        if submit_job_msg:
            logger.info(submit_job_msg)


def monte_carlo(desc_file, csv_file, no_submit=False):
    """

    :param :py:class:`pathlib.Path` desc_file:
    :param :py:class:`pathlib.Path` csv_file:
    :param boolean no_submit:

    :return:
    :rtype: str
    """
    job_desc = nemo_cmd.prepare.load_run_desc(desc_file)
    job_id = nemo_cmd.prepare.get_run_desc_value(job_desc, ("job id",))
    forcing_dir = nemo_cmd.prepare.get_run_desc_value(
        job_desc, ("paths", "forcing directory"), expand_path=True, resolve_path=True,
    )
    runs_dir = nemo_cmd.prepare.get_run_desc_value(
        job_desc, ("paths", "runs directory"), expand_path=True, resolve_path=True,
    )
    job_dir = runs_dir / f"{job_id}_{arrow.now().format('YYYY-MM-DDTHHmmss')}"
    runs = _get_runs_info(csv_file)
    ## TODO: Calculate walltime from number of runs and number of cores
    run_walltime = nemo_cmd.prepare.get_run_desc_value(
        job_desc, ("run walltime",), run_dir=job_dir
    )
    run_walltime = datetime.timedelta(seconds=run_walltime)
    walltime = mohid_cmd.run.td_to_hms(run_walltime)
    cookiecutter_context = {
        "job_id": job_id,
        "job_dir": job_dir,
        "account": nemo_cmd.prepare.get_run_desc_value(
            job_desc, ("account",), run_dir=job_dir
        ),
        "email": nemo_cmd.prepare.get_run_desc_value(
            job_desc, ("email",), run_dir=job_dir
        ),
        "nodes": nemo_cmd.prepare.get_run_desc_value(
            job_desc, ("nodes",), run_dir=job_dir
        ),
        "ntasks_per_node": nemo_cmd.prepare.get_run_desc_value(
            job_desc, ("tasks per node",), run_dir=job_dir
        ),
        "mem_per_cpu": nemo_cmd.prepare.get_run_desc_value(
            job_desc, ("mem per cpu",), run_dir=job_dir
        ),
        "runs_per_job": nemo_cmd.prepare.get_run_desc_value(
            job_desc, ("runs per glost job",), run_dir=job_dir
        ),
        "walltime": walltime,
        "mohid_cmd": nemo_cmd.prepare.get_run_desc_value(
            job_desc, ("mohid command",), run_dir=job_dir
        ),
    }
    cookiecutter.main.cookiecutter(
        os.fspath(Path(__file__).parent.parent / "cookiecutter"),
        no_input=True,
        output_dir=job_dir,
        extra_context=cookiecutter_context,
    )
    shutil.copy2(desc_file, job_dir)
    shutil.copy2(csv_file, job_dir)
    nemo_cmd.prepare.record_vcs_revisions(job_desc, job_dir)
    mohid_config = nemo_cmd.prepare.get_run_desc_value(
        job_desc,
        ("paths", "mohid config"),
        expand_path=True,
        resolve_path=True,
        run_dir=job_dir,
    )
    tmpl_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.fspath(mohid_config / "templates"))
    )
    _render_make_hdf5_yamls(job_id, job_dir, forcing_dir, runs, tmpl_env)
    _render_mohid_run_yamls(
        job_id, job_dir, forcing_dir, runs_dir, mohid_config, runs, tmpl_env
    )
    _render_model_dats(job_dir, runs, tmpl_env)
    _render_lagrangian_dats(job_dir, runs, tmpl_env)
    logger.info(f"job directory created: {job_dir}")
    if no_submit:
        return
    sbatch_cmd = f"sbatch {job_dir / 'glost-job.sh'}"
    submit_job_msg = subprocess.run(
        shlex.split(sbatch_cmd),
        check=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
    ).stdout
    return submit_job_msg


def _get_runs_info(csv_file):
    """
    :param :py:class:`pathlib.Path` csv_file:

    :rtype: :py:class:`pandas.DataFrame`
    """
    return pandas.read_csv(csv_file, skipinitialspace=True, parse_dates=[0])


def _render_make_hdf5_yamls(job_id, job_dir, forcing_dir, runs, tmpl_env):
    """
    :param str job_id:
    :param :py:class:`pathlib.Path` job_dir:
    :param :py:class:`pathlib.Path` forcing_dir:
    :param :py:class:`pandas.DataFrame` runs:
    :param :py:class:`jinja2.Environment` tmpl_env:
    """
    tmpl = tmpl_env.get_template("make-hdf5.yaml")
    context = {"forcing_dir": forcing_dir}
    for i, run in runs.iterrows():
        (job_dir / "forcing-yaml" / f"{job_id}-make-hdf5-{i}.yaml").write_text(
            tmpl.render(context)
        )


def _render_mohid_run_yamls(
    job_id, job_dir, forcing_dir, runs_dir, mohid_config, runs, tmpl_env
):
    """
    :param str job_id:
    :param :py:class:`pathlib.Path` job_dir:
    :param :py:class:`pathlib.Path` forcing_dir:
    :param :py:class:`pathlib.Path` runs_dir:
    :param :py:class:`pathlib.Path` mohid_config:
    :param :py:class:`pandas.DataFrame` runs:
    :param :py:class:`jinja2.Environment` tmpl_env:
    """

    tmpl = tmpl_env.get_template("mohid-run.yaml")
    context = {
        "job_id": job_id,
        "job_dir": job_dir,
        "forcing_dir": forcing_dir,
        "runs_dir": runs_dir,
    }
    for i, run in runs.iterrows():
        start_date = arrow.get(run.spill_date_hour.date())
        end_date = start_date.shift(days=+run.run_days)
        context.update(
            {
                "run_number": i,
                "start_ddmmmyy": start_date.format("DDMMMYY").lower(),
                "end_ddmmmyy": end_date.format("DDMMMYY").lower(),
                "Lagrangian_template": Path(run.Lagrangian_template).stem,
                "mohid_config": mohid_config,
            }
        )
        (job_dir / "mohid-yaml" / f"{job_id}-{i}.yaml").write_text(tmpl.render(context))


def _render_model_dats(job_dir, runs, tmpl_env):
    """
    :param :py:class:`pathlib.Path` job_dir:
    :param :py:class:`pandas.DataFrame` runs:
    :param :py:class:`jinja2.Environment` tmpl_env:
    """
    tmpl = tmpl_env.get_template("Model.dat")
    for i, run in runs.iterrows():
        ## TODO: Ensure that end_date - start_date are a multiple of DT value in template
        ##       This depends on how we handle spill hour.
        start_date = arrow.get(run.spill_date_hour.date())
        end_date = start_date.shift(days=+run.run_days - 1)
        context = {
            "start_yyyy_mm_dd": start_date.format("YYYY MM DD"),
            "end_yyyy_mm_dd": end_date.format("YYYY MM DD"),
        }
        (job_dir / "mohid-yaml" / f"Model-{i}.dat").write_text(tmpl.render(context))


def _render_lagrangian_dats(job_dir, runs, tmpl_env):
    """
    :param :py:class:`pathlib.Path` job_dir:
    :param :py:class:`pandas.DataFrame` runs:
    :param :py:class:`jinja2.Environment` tmpl_env:
    """
    for i, run in runs.iterrows():
        lagrangian_template = Path(run.Lagrangian_template)
        tmpl = tmpl_env.get_template(os.fspath(lagrangian_template))
        context = {
            "spill_lon": run.spill_lon,
            "spill_lat": run.spill_lat,
        }
        lagrangian_dat = f"{lagrangian_template.stem}-{i}.dat"
        (job_dir / "mohid-yaml" / lagrangian_dat).write_text(tmpl.render(context))
