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
"""Fixture for MOHID-Cmd test suite.
"""
import textwrap

import pytest
import yaml


@pytest.fixture()
def run_desc(tmp_path):
    mohid_repo = tmp_path / "MIDOSS-MOHID-CODE"
    mohid_repo.mkdir()
    mohid_bin = mohid_repo / "Solutions" / "linux" / "bin"
    mohid_bin.mkdir(parents=True)
    mohid_exe = mohid_bin / "MohidWater.exe"
    mohid_exe.write_bytes(b"")

    forcing = tmp_path.joinpath("MIDOSS", "forcing", "HRDPS")
    forcing.mkdir(parents=True)
    wind_hdf5 = forcing / "hrdps_20181211_20181218.hdf5"
    wind_hdf5.write_bytes(b"")

    grid = tmp_path / "MIDOSS-MOHID-grid"
    grid.mkdir()
    bathy = grid / "SalishSeaCast_bathymetry.dat"
    bathy.write_bytes(b"")

    runs_dir = tmp_path / "runs_dir"
    runs_dir.mkdir()

    settings = tmp_path / "MIDOSS-MOHID-config" / "settings"
    settings.mkdir(parents=True)
    dat_files = (
        "Model.dat",
        "Lagrangian_DieselFuel_refined.dat",
        "Geometry.dat",
        "Atmosphere.dat",
        "Hydrodynamic.dat",
        "InterfaceSedimentWater.dat",
        "InterfaceWaterAir.dat",
        "Tide.dat",
        "Turbulence.dat",
        "WaterProperties.dat",
        "Waves.dat",
    )
    dat_paths = {}
    for dat_file in dat_files:
        dat_paths[dat_file] = settings / dat_file
        dat_paths[dat_file].write_text("")

    p_run_desc = tmp_path / "mohid.yaml"
    p_run_desc.write_text(
        textwrap.dedent(
            f"""\
            run_id: MarathassaConstTS
            email: you@example.com
            account: def-allen
            walltime: "1:30:00"

            paths:
              mohid repo: {mohid_repo}
              runs directory: {runs_dir}

            forcing:
              winds.hdf5: {wind_hdf5}

            bathymetry: {bathy}

            run data files:
              IN_MODEL: {dat_paths["Model.dat"]}
              PARTIC_DATA: {dat_paths["Lagrangian_DieselFuel_refined.dat"]}
              DOMAIN: {dat_paths["Geometry.dat"]}
              SURF_DAT: {dat_paths["Atmosphere.dat"]}
              IN_DAD3D: {dat_paths["Hydrodynamic.dat"]}
              BOT_DAT: {dat_paths["InterfaceSedimentWater.dat"]}
              AIRW_DAT: {dat_paths["InterfaceWaterAir.dat"]}
              IN_TIDES: {dat_paths["Tide.dat"]}
              IN_TURB: {dat_paths["Turbulence.dat"]}
              DISPQUAL: {dat_paths["WaterProperties.dat"]}
              WAVES_DAT: {dat_paths["Waves.dat"]}

            vcs revisions:
              git:
                - MIDOSS-MOHID-config
            """
        )
    )
    with p_run_desc.open("rt") as f:
        run_desc = yaml.safe_load(f)
    return run_desc
