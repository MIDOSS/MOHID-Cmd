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
"""MOHID-Cmd command plug-in for gather sub-command.

Gather results files from a MIDOSS-MOHID run into a specified directory.
"""
import logging
from pathlib import Path
import shutil

import cliff.command
import nemo_cmd

logger = logging.getLogger(__name__)


class Gather(cliff.command.Command):
    """Gather results files from a MIDOSS-MOHID run.
    """

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.description = """
            Gather the results files from the MIDOSS-MOHID run in the present working
            directory into files in RESULTS_DIR.
            The run description YAML file,
            `nomfich.dat` file,
            and other files that define the run are also gathered into
            RESULTS_DIR.

            If RESULTS_DIR does not exist it will be created.
        """
        parser.add_argument(
            "results_dir",
            type=Path,
            metavar="RESULTS_DIR",
            help="directory to store results into",
        )
        return parser

    def take_action(self, parsed_args):
        """Execute the `mohid gather` sub-command.

        Gather the results files from a MIDOSS-MOHID run into a results directory.

        The run description file,
        `nomfich.dat` file,
        and other files that define the run are also gathered into the
        directory given by `parsed_args.results_dir`.
        """
        gather(parsed_args.results_dir)


def gather(results_dir):
    """Move all of the files and directories from the present working directory
    into results_dir.

    If results_dir doesn't exist, create it.

    Delete any symbolic links and sub-directories so that the present working directory is empty.

    :param results_dir: Path of the directory into which to store the run
                        results.
    :type results_dir: :py:class:`pathlib.Path`
    """
    results_dir = nemo_cmd.resolved_path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    symlinks = {p for p in Path.cwd().glob("*") if p.is_symlink()}
    res_files = {p for p in (Path.cwd() / "res").glob("*")}
    try:
        _move_results(results_dir, symlinks, res_files)
    except Exception:
        raise


def _move_results(results_dir, symlinks, res_files):
    """
    :param :py:class:`pathlib.Path` results_dir:
    :param set symlinks:
    :param set res_files:
    """
    tmp_run_dir = Path.cwd()
    if tmp_run_dir.samefile(results_dir):
        return
    logger.info("Moving run definition and results files...")
    for p in tmp_run_dir.glob("*"):
        if p not in symlinks and p != tmp_run_dir / "res":
            _move_file(tmp_run_dir, p, results_dir)
    for p in res_files:
        _move_file(tmp_run_dir, p, results_dir)
    _delete_symlinks_and_res_dir(symlinks)


def _move_file(tmp_run_dir, path, results_dir):
    """
    :param :py:class:`pathlib.Path` tmp_run_dir:
    :param :py:class:`pathlib.Path` path:
    :param :py:class:`pathlib.Path` results_dir:
    """
    src = path.relative_to(tmp_run_dir)
    logger.info(f"Moving {src} to {results_dir / src.name}")
    shutil.move(src, results_dir / src.name)


def _delete_symlinks_and_res_dir(symlinks):
    """
    :param set symlinks:
    """
    logger.info("Deleting symbolic links...")
    for ln in symlinks:
        ln.unlink()
    logger.info("Deleting files left in res/...")
    cwd = Path.cwd()
    for p in (cwd / "res").glob("*"):
        p.unlink()
    logger.info("Deleting res/...")
    (cwd / "res").rmdir()
