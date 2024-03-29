#  Copyright 2018-2021 the MIDOSS project contributors, The University of British Columbia,
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
import shlex
import subprocess
import textwrap
from pathlib import Path

import cliff.command
import nemo_cmd.prepare

import mohid_cmd.prepare

logger = logging.getLogger(__name__)


class Run(cliff.command.Command):
    """Prepare, execute, and gather results from a MIDOSS-MOHID model run."""

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
            help="Run description YAML file",
        )
        parser.add_argument(
            "results_dir",
            metavar="RESULTS_DIR",
            type=Path,
            help="Directory to store results into",
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
            help="Don't show the run directory path or job submission message",
        )
        parser.add_argument(
            "--tmp-run-dir",
            dest="tmp_run_dir",
            default="",
            help="""
            Name to use for temporary run directory.
            This is intended for use in Monte Carlo runs for which it is necessary to
            have an a priori known temporary run directory name.
            Normally, the temporary run directory name is automatically generated based on
            the run id and the date/time at which :kbd:`mohid run` is executed.
            """,
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
            tmp_run_dir=parsed_args.tmp_run_dir,
        )
        if submit_job_msg and not parsed_args.quiet:
            logger.info(submit_job_msg)


def run(desc_file, results_dir, no_submit=False, quiet=False, tmp_run_dir=""):
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
    :type results_dir: :py:class:`pathlib.Path`

    :param boolean no_submit: Prepare the temporary run directory,
                              and the run script to execute the MOHID run,
                              but don't submit the run to the queue.

    :param boolean quiet: Don't show the run directory path message;
                          the default is to show the temporary run directory
                          path.

    :param string tmp_run_dir: Name to use for temporary run directory.

    :returns: Message generated by queue manager upon submission of the
              run script.
    :rtype: str
    """
    tmp_run_dir = mohid_cmd.prepare.prepare(desc_file, tmp_run_dir)
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
    results_dir.mkdir(parents=True, exist_ok=True)
    if no_submit:
        return
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
    walltime = td_to_hms(td)
    sbatch_directives = textwrap.dedent(
        f"""\
        #SBATCH --job-name={run_id}
        #SBATCH --account={account}
        #SBATCH --mail-user={email}
        #SBATCH --mail-type=ALL
        #SBATCH --cpus-per-task=1
        #SBATCH --mem-per-cpu=14500m
        #SBATCH --time={walltime}
        #SBATCH --output={results_dir/'stdout'}
        #SBATCH --error={results_dir/'stderr'}

        if ! test -z $SLURM_CPUS_PER_TASK
        then
          export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
        fi
        """
    )
    return sbatch_directives


def td_to_hms(timedelta):
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
    defns = textwrap.dedent(
        f"""\
        RUN_ID="{run_id}"
        RUN_DESC="{desc_file}"
        WORK_DIR="{tmp_run_dir}"
        RESULTS_DIR="{results_dir}"
        HDF5_TO_NETCDF4="{user_local_bin}/hdf5-to-netcdf4"
        GATHER="{user_local_bin}/mohid gather"
        """
    )
    return defns


def _modules():
    """
    :rtype: str
    """
    modules = textwrap.dedent(
        """\
        module load StdEnv/2016.4
        module load proj4-fortran/1.0
        module load python/3.8.2
        module load nco/4.6.6
        """
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
    partic_data = nemo_cmd.prepare.get_run_desc_value(
        run_desc, ("run data files", "PARTIC_DATA"), resolve_path=True
    )
    script = textwrap.dedent(
        f"""\
        mkdir -p ${{RESULTS_DIR}}
        cd ${{WORK_DIR}}
        echo "working dir: $(pwd)" >${{RESULTS_DIR}}/stdout

        echo "Starting run at $(date)" >>${{RESULTS_DIR}}/stdout
        {str(mohid_exe)} >>${{RESULTS_DIR}}/stdout 2>>${{RESULTS_DIR}}/stderr
        MOHID_EXIT_CODE=$?
        echo "Ended run at $(date)" >>${{RESULTS_DIR}}/stdout

        TMPDIR="${{SLURM_TMPDIR}}"
        LAGRANGIAN="{partic_data.stem}_${{RUN_ID}}"
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

        echo "Rename mass balance file to MassBalance_${{RUN_ID}}.sro" >>${{RESULTS_DIR}}/stdout
        mv -v ${{WORK_DIR}}/resOilOutput.sro ${{WORK_DIR}}/MassBalance_${{RUN_ID}}.sro >>${{RESULTS_DIR}}/stdout

        echo "Delete large unused output files"  >>${{RESULTS_DIR}}/stdout
        rm -v ${{WORK_DIR}}/res/Turbulence*.hdf5 ${{WORK_DIR}}/res*.elf5 ${{WORK_DIR}}/res*.ptf

        echo "Results gathering started at $(date)" >>${{RESULTS_DIR}}/stdout
        ${{GATHER}} ${{RESULTS_DIR}} --debug >>${{RESULTS_DIR}}/stdout 2>>${{RESULTS_DIR}}/stderr
        echo "Results gathering ended at $(date)" >>${{RESULTS_DIR}}/stdout
        """
    )
    return script


def _fix_permissions():
    script = textwrap.dedent(
        """\
        chmod -v go+rx ${RESULTS_DIR} >>${RESULTS_DIR}/stdout
        chmod -v g+rw ${RESULTS_DIR}/* >>${RESULTS_DIR}/stdout
        chmod -v o+r ${RESULTS_DIR}/* >>${RESULTS_DIR}/stdout
        """
    )
    return script


def _cleanup():
    script = textwrap.dedent(
        """\
        echo "Deleting run directory" >>${RESULTS_DIR}/stdout
        rmdir -v $(pwd) >>${RESULTS_DIR}/stdout
        echo "Finished at $(date)" >>${RESULTS_DIR}/stdout
        exit ${MOHID_EXIT_CODE}
        """
    )
    return script
