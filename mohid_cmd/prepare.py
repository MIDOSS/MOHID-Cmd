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
"""MOHID-Cmd command plug-in for prepare sub-command.

Sets up the necessary symbolic links for a MIDOSS-MOHID run
in a specified directory and changes the pwd to that directory.
"""
import logging
from pathlib import Path
import shutil

import cliff.command
import nemo_cmd.prepare

logger = logging.getLogger(__name__)


class Prepare(cliff.command.Command):
    """Set up the MIDOSS-MOHID run described in DESC_FILE and print the path of the temporary run directory.
    """

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "desc_file",
            metavar="DESC_FILE",
            type=Path,
            help="run description YAML file",
        )
        parser.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="don't show the run directory path on completion",
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
        """Execute the `salishsea prepare` sub-command.

        A temporary run directory is created.
        Symbolic links and file copies are created in that directory based on the files and
        directories specified in the run description YAML file for a MIDOSS-MOHID run.
        The output of :command:`hg parents` is recorded in the directory
        for the MIDOSS-MOHID code and MIDOSS-MOHID-config repos that the symlinks point to.
        The path to the temporary run directory is logged to the console on completion
        of the set-up.
        """
        tmp_run_dir = prepare(parsed_args.desc_file, parsed_args.tmp_run_dir)
        if not parsed_args.quiet:
            logger.info(f"Created temporary run directory: {tmp_run_dir}")
        return tmp_run_dir


def prepare(desc_file, tmp_run_dir=""):
    """Create and prepare the temporary run directory.

    The temporary run directory is created with a unique name composed of the run id
    and an ISO-format date/time stamp.
    Symbolic links and file copies are created in that directory based on the files and
    directories specified in the run description YAML file for a MIDOSS-MOHID run.
    The output of :command:`hg parents` is recorded in the directory
    for the MIDOSS-MOHID code and MIDOSS-MOHID-config repos that the symlinks point to.
    The path to the temporary run directory is returned.

    :param desc_file: File path/name of the YAML run description file.
    :type desc_file: :py:class:`pathlib.Path`

    :param string tmp_run_dir: Name to use for temporary run directory.

    :returns: Path of the temporary run directory
    :rtype: :py:class:`pathlib.Path`
    """
    run_desc = nemo_cmd.prepare.load_run_desc(desc_file)
    mohid_exe = _check_mohid_exec(run_desc)
    tmp_run_dir = _make_run_dir(run_desc, tmp_run_dir)
    (tmp_run_dir / mohid_exe.name).symlink_to(mohid_exe)
    shutil.copy2(desc_file, tmp_run_dir / desc_file.name)
    _make_forcing_links(run_desc, tmp_run_dir)
    _make_nomfich(run_desc, tmp_run_dir)
    mohid_repo = nemo_cmd.prepare.get_run_desc_value(
        run_desc, ("paths", "mohid repo"), resolve_path=True
    )
    nemo_cmd.prepare.write_repo_rev_file(
        mohid_repo, tmp_run_dir, nemo_cmd.prepare.get_hg_revision
    )
    nemo_cmd.prepare.record_vcs_revisions(run_desc, tmp_run_dir)
    return tmp_run_dir


def _check_mohid_exec(run_desc):
    """Calculate absolute path of the MOHID executable.

    Confirm that the MOHID executable exists, raising a SystemExit
    exception if it does not.

    :param dict run_desc: Run description dictionary.

    :returns: Absolute path of MOHID executable.
    :rtype: :py:class:`pathlib.Path`

    :raises: :py:exc:`SystemExit` with exit code 2
    """
    mohid_repo = nemo_cmd.prepare.get_run_desc_value(
        run_desc, ("paths", "mohid repo"), resolve_path=True
    )
    mohid_exe = mohid_repo / Path("Solutions/linux/bin/MohidWater.exe")
    if not mohid_exe.exists():
        logger.error(f"{mohid_exe} not found - did you forget to build it?")
        raise SystemExit(2)
    return mohid_exe


def _make_run_dir(run_desc, tmp_run_dir):
    """
    :param desc_file: File path/name of the YAML run description file.
    :type desc_file: :py:class:`pathlib.Path`

    :param string tmp_run_dir: Name to use for temporary run directory.

    :returns: Path of the temporary run directory
    :rtype: :py:class:`pathlib.Path`
    """
    if not tmp_run_dir:
        return nemo_cmd.prepare.make_run_dir(run_desc)
    runs_dir = nemo_cmd.prepare.get_run_desc_value(
        run_desc, ("paths", "runs directory"), resolve_path=True
    )
    run_dir = runs_dir / tmp_run_dir
    run_dir.mkdir()
    return run_dir


def _make_forcing_links(run_desc, tmp_run_dir):
    """
    :param dict run_desc:
    :param :py:class:`pathlib.Path` tmp_run_dir:
    """
    link_names = nemo_cmd.prepare.get_run_desc_value(
        run_desc, ("forcing",), run_dir=tmp_run_dir
    )
    for link_name in link_names:
        source = nemo_cmd.prepare.get_run_desc_value(
            run_desc, ("forcing", link_name), expand_path=True, fatal=False
        )
        if not source.exists():
            logger.error(
                f"{source} not found; cannot create symlink - "
                f"please check the forcing paths and file names in your run description file"
            )
            nemo_cmd.prepare.remove_run_dir(tmp_run_dir)
            raise SystemExit(2)
        (tmp_run_dir / link_name).symlink_to(source.resolve())


def _make_nomfich(run_desc, tmp_run_dir):
    """
    :param dict run_desc:
    :param :py:class:`pathlib.Path` tmp_run_dir:
    """
    bathymetry = nemo_cmd.prepare.get_run_desc_value(
        run_desc,
        ("bathymetry",),
        expand_path=True,
        resolve_path=True,
        run_dir=tmp_run_dir,
    )
    results_dir = tmp_run_dir / "res"
    results_dir.mkdir()
    nomfich = {"IN_BATIM": bathymetry, "ROOT": results_dir}
    run_data_files = nemo_cmd.prepare.get_run_desc_value(
        run_desc, ("run data files",), run_dir=tmp_run_dir
    )
    run_id = nemo_cmd.prepare.get_run_desc_value(
        run_desc, ("run_id",), run_dir=tmp_run_dir
    )
    hdf_files = {
        "PARTIC_DATA": "PARTIC_HDF",
        "SURF_DAT": "SURF_HDF",
        "AIRW_DAT": "AIRW_HDF",
        "IN_TURB": "TURB_HDF",
        "DISPQUAL": "EUL_HDF",
        "WAVES_DAT": "WAVES_HDF",
    }
    for key, path in run_data_files.items():
        dat_path = nemo_cmd.expanded_path(path)
        nomfich.update({key: dat_path})
        if key in hdf_files:
            hdf_file = results_dir / f"{dat_path.stem}_{run_id}.hdf"
            nomfich.update({hdf_files[key]: hdf_file})
    with (tmp_run_dir / "nomfich.dat").open("wt") as f:
        for key, value in nomfich.items():
            f.write(f"{key:<11} : {value}\n")
