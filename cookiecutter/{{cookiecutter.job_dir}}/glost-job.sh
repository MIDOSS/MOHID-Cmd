#!/bin/bash

#SBATCH --job-name={{ cookiecutter.job_id }}
#SBATCH --account={{ cookiecutter.account }}
#SBATCH --mail-user={{ cookiecutter.email }}
#SBATCH --mail-type=ALL
#SBATCH --nodes={{ cookiecutter.nodes }}
#SBATCH --ntasks-per-node={{ cookiecutter.ntasks_per_node }}
#SBATCH --mem-per-cpu={{ cookiecutter.mem_per_cpu }}
#SBATCH --exclude=gra[801-803]
#SBATCH --time={{ cookiecutter.walltime }}
#SBATCH --output={{ cookiecutter.job_dir }}/glost-job.stdout
#SBATCH --error={{ cookiecutter.job_dir }}/glost-job.stderr

module load StdEnv/2016.4
module load glost/0.3.1
module load python/3.8.2
module load proj4-fortran/1.0
module load nco/4.6.6

export MONTE_CARLO={{ cookiecutter.job_dir }}

echo "Starting glost at $(date)"
srun glost_launch {{ cookiecutter.job_dir }}/glost-tasks.txt
echo "Ended glost at $(date)"
