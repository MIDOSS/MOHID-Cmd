#!/bin/bash

#SBATCH --job-name={{ cookiecutter.run_id }}
#SBATCH --account={{ cookiecutter.account }}
#SBATCH --mail-user={{ cookiecutter.email }}
#SBATCH --mail-type=ALL
#SBATCH --nodes={{ cookiecutter.nodes }}
#SBATCH --ntasks-per-node={{ cookiecutter.ntasks_per_node }}
#SBATCH --mem-per-cpu={{ cookiecutter.mem_per_cpu }}
#SBATCH --time={{ cookiecutter.walltime }}
#SBATCH --output={{ cookiecutter.job_dir }}glost-job.stdout
#SBATCH --error={{ cookiecutter.job_dir }}glost-job.stderr

module load glost/0.3.1
module load python/3.7
module load proj4-fortran/1.0
module load nco/4.6.6

export MONTE_CARLO/={{ cookiecutter.job_dir }}

echo "Starting glost at $(date)"
srun glost_launch {{ cookiecutter.job_dir }}/glost-tasks.txt
echo "Ended glost at $(date)"
