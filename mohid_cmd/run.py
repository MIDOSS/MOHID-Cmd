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
"""MOHID-Cmd command plug-in for run sub-command.

Prepare for, execute, and gather the results of a run of the MIDOSS-MOHID model.
"""
import datetime
import logging
import os
from pathlib import Path
import shlex
import subprocess

import cliff.command

from mohid_cmd import api
import nemo_cmd.prepare

logger = logging.getLogger(__name__)


class Run(cliff.command.Command):
    """Prepare, execute, and gather results from a MIDOSS-MOHID model run.
    """

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.description = """
            Prepare, execute, and gather the results from a MIDOSS-MOHID
            run described in DESC_FILE.
            The results files from the run are gathered in RESULTS_DIR.

            If RESULTS_DIR does not exist it will be created.
        """
        parser.add_argument(
            "desc_file",
            metavar="DESC_FILE",
            type=Path,
            help="run description YAML file",
        )
        parser.add_argument(
            "results_dir",
            metavar="RESULTS_DIR",
            type=Path,
            help="directory to store results into",
        )
        parser.add_argument(
            "--no-submit",
            dest="no_submit",
            action="store_true",
            help="""
            Prepare the temporary run directory, and the bash script to 
            execute the MOHID run, but don't submit the run to the queue.
            This is useful during development runs when you want to hack on 
            the bash script and/or use the same temporary run directory 
            more than once.
            """,
        )
        parser.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="don't show the run directory path or job submission message",
        )
        return parser

    def take_action(self, parsed_args):
        """Execute the `mohid run` sub-coomand.

        The message generated upon submission of the run to the queue
        manager is logged to the console.

        :param parsed_args: Arguments and options parsed from the command-line.
        :type parsed_args: :class:`argparse.Namespace` instance
        """
        submit_job_msg = run(
            parsed_args.desc_file,
            parsed_args.results_dir,
            no_submit=parsed_args.no_submit,
            quiet=parsed_args.quiet,
        )
        if submit_job_msg and not parsed_args.quiet:
            logger.info(submit_job_msg)


def run(desc_file, results_dir, no_submit=False, quiet=False):
    """Create and populate a temporary run directory, and a run script,
    and submit the run to the queue manager.

    The temporary run directory is created and populated via the
    :func:`mohid_cmd.api.prepare` API function.
    The run script is stored in :file:`MOHID.sh` in the temporary run directory.
    That script is submitted to the queue manager in a subprocess.

    :param desc_file: File path/name of the YAML run description file.
    :type desc_file: :py:class:`pathlib.Path`

    :param results_dir: Path of the directory in which to store the run results;
                        it will be created if it does not exist.
    :type desc_file: :py:class:`pathlib.Path`

    :param boolean no_submit: Prepare the temporary run directory,
                              and the run script to execute the MOHID run,
                              but don't submit the run to the queue.

    :param boolean quiet: Don't show the run directory path message;
                          the default is to show the temporary run directory
                          path.

    :returns: Message generated by queue manager upon submission of the
              run script.
    :rtype: str
    """
    tmp_run_dir = api.prepare(desc_file)
    if not quiet:
        logger.info(f"Created temporary run directory {tmp_run_dir}")
    run_desc = nemo_cmd.prepare.load_run_desc(desc_file)
    results_dir = nemo_cmd.resolved_path(results_dir)
    run_script = _build_run_script(run_desc, desc_file, results_dir, tmp_run_dir)
    run_script_file = tmp_run_dir / "MOHID.sh"
    with run_script_file.open("wt") as f:
        f.write(run_script)
    if not quiet:
        logger.info(f"Wrote job run script to {run_script_file}")
    if no_submit:
        return
    results_dir.mkdir(parents=True, exist_ok=True)
    sbatch_cmd = f"sbatch {run_script_file}"
    submit_job_msg = subprocess.run(
        shlex.split(sbatch_cmd),
        check=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
    ).stdout
    return submit_job_msg


def _build_run_script(run_desc, desc_file, results_dir, tmp_run_dir):
    """
    :param dict run_desc:
    :param :py:class:`pathlib.Path` desc_file:
    :param :py:class:`pathlib.Path` results_dir:
    :param :py:class:`pathlib.Path` tmp_run_dir:

    :rtype: str
    """
    run_script = "#!/bin/bash\n"
    run_script = "\n".join(
        (
            run_script,
            _sbatch_directives(run_desc, results_dir),
            _definitions(run_desc, desc_file, results_dir, tmp_run_dir),
            _modules(),
            _execute(run_desc),
            _fix_permissions(),
            _cleanup(),
        )
    )
    return run_script


def _sbatch_directives(run_desc, results_dir):
    """
    :param dict run_desc:
    :param :py:class:`pathlib.Path` results_dir:

    :rtype: str
    """
    run_id = nemo_cmd.prepare.get_run_desc_value(run_desc, ("run_id",))
    try:
        email = nemo_cmd.prepare.get_run_desc_value(run_desc, ("email",), fatal=False)
    except KeyError:
        email = "{user}@eoas.ubc.ca".format(user=os.getenv("USER"))
    try:
        account = nemo_cmd.prepare.get_run_desc_value(
            run_desc, ("account",), fatal=False
        )
    except KeyError:
        account = "rrg-allen"
        logger.info(
            f"No account found in run description YAML file, "
            f"so assuming {account}. If sbatch complains you can specify a "
            f"different account with a YAML line like account: def-allen"
        )
    try:
        td = datetime.timedelta(
            seconds=nemo_cmd.prepare.get_run_desc_value(run_desc, ("walltime",))
        )
    except TypeError:
        t = datetime.datetime.strptime(
            nemo_cmd.prepare.get_run_desc_value(run_desc, ("walltime",)), "%H:%M:%S"
        ).time()
        td = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    walltime = _td_to_hms(td)
    sbatch_directives = (
        f"#SBATCH --job-name={run_id}\n"
        f"#SBATCH --account={account}\n"
        f"#SBATCH --mail-user={email}\n"
        f"#SBATCH --mail-type=ALL\n"
        f"#SBATCH --cpus-per-task=1\n"
        f"#SBATCH --mem-per-cpu=20000m\n"
        f"#SBATCH --time={walltime}\n"
        f"#SBATCH --output={results_dir/'stdout'}\n"
        f"#SBATCH --error={results_dir/'stderr'}\n"
        f"\n"
        f"export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK\n"
    )
    return sbatch_directives


def _td_to_hms(timedelta):
    """Return a string that is the timedelta value formatted as H:M:S
    with leading zeros on the minutes and seconds values.

    :param :py:obj:datetime.timedelta timedelta: Time interval to format.

    :returns: H:M:S string with leading zeros on the minutes and seconds
              values.
    :rtype: str
    """
    seconds = int(timedelta.total_seconds())
    periods = (("hour", 60 * 60), ("minute", 60), ("second", 1))
    hms = []
    for period_name, period_seconds in periods:
        period_value, seconds = divmod(seconds, period_seconds)
        hms.append(period_value)
    return f"{hms[0]}:{hms[1]:02d}:{hms[2]:02d}"


def _definitions(run_desc, desc_file, results_dir, tmp_run_dir):
    """
    :param dict run_desc:
    :param :py:class:`pathlib.Path` desc_file:
    :param :py:class:`pathlib.Path` results_dir:
    :param :py:class:`pathlib.Path` tmp_run_dir:

    :rtype: str
    """
    user_local_bin = "${HOME}/.local/bin"
    run_id = run_desc["run_id"]
    defns = (
        f'RUN_ID="{run_id}"\n'
        f'RUN_DESC="{desc_file}"\n'
        f'WORK_DIR="{tmp_run_dir}"\n'
        f'RESULTS_DIR="{results_dir}"\n'
        f'HDF5_TO_NETCDF4="{user_local_bin}/hdf5-to-netcdf4"\n'
        f'GATHER="${{HOME}}/.local/bin/mohid gather"\n'
    )
    return defns


def _modules():
    """
    :rtype: str
    """
    modules = (
        "module load proj4-fortran/1.0\n"
        "module load python/3.7.0\n"
        "module load nco/4.6.6\n"
    )
    return modules


def _execute(run_desc):
    """
    :param dict run_desc:

    :rtype: str
    """
    mohid_repo = nemo_cmd.prepare.get_run_desc_value(
        run_desc, ("paths", "mohid repo"), resolve_path=True
    )
    mohid_exe = mohid_repo / Path("Solutions/linux/bin/MohidWater.exe")
    script = (
        f"mkdir -p ${{RESULTS_DIR}}\n"
        f"cd ${{WORK_DIR}}\n"
        f'echo "working dir: $(pwd)"\n'
        f"\n"
        f'echo "Starting run at $(date)"\n'
        f"{str(mohid_exe)}\n"
        f"MOHID_EXIT_CODE=$?\n"
        f'echo "Ended run at $(date)"\n'
        f"\n"
        f'echo "Results hdf5 to netCDF4 conversion started at $(date)"\n'
        f"${{HDF5_TO_NETCDF4}} ${{WORK_DIR}}/res/Lagrangian_${{RUN_ID}}.hdf5 ${{WORK_DIR}}/Lagrangian_${{RUN_ID}}.nc\n"
        f'echo "Results hdf5 to netCDF4 conversion ended at $(date)"\n'
        f"\n"
        f'echo "Results gathering started at $(date)"\n'
        f"${{GATHER}} ${{RESULTS_DIR}} --debug\n"
        f'echo "Results gathering ended at $(date)"\n'
    )
    return script


def _fix_permissions():
    script = (
        f"chmod go+rx ${{RESULTS_DIR}}\n"
        f"chmod g+rw ${{RESULTS_DIR}}/*\n"
        f"chmod o+r ${{RESULTS_DIR}}/*\n"
    )
    return script


def _cleanup():
    script = (
        f'echo "Deleting run directory" >>${{RESULTS_DIR}}/stdout\n'
        f"rmdir $(pwd)\n"
        f'echo "Finished at $(date)" >>${{RESULTS_DIR}}/stdout\n'
        f"exit ${{MPIRUN_EXIT_CODE}}\n"
    )
    return script
