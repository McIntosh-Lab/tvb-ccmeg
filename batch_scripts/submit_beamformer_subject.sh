#!/bin/bash
#SBATCH --output=./logs/proc_out/job_output_%j.txt
#SBATCH --error=./logs/proc_err/job_error_%j.txt
#SBATCH --ntasks=1
#SBATCH --time=01:00:00
#SBATCH --mem=64000M
#SBATCH --account=rrg-rmcintos

# submit_subject.sh is used to excecute a python meg pipeline for a given 
# subject directory, from that subjects parent directory.
#
# Usage:
#	./submit_subject.sh <subject_directory_name>
#
#
#	|- parent_directory
#	| |- subject_directory_name
#       | ... 
#       | ...
#
# Which pipeline is used is determined by the REPO_DIRECTORY variable below. 
# The top level of the directory should contain a pipeline.py or 
# pipeline_test.py file that takes as argument the name of a subject directory
# to be processed. E.g.
# 
# python <REPO_DIRECTORY>/pipeline.py" <SUBJECT_DIRECTORY>
#

if [ $# -ne 2 ]; then
    echo "Usage: $0 <pipeline_repo> <subject_directory>"
    exit 1
fi

PIPELINE_REPO=$1
SUBJECT_DIRECTORY=$2

# Set up free surfer
echo "Setting up FreeSurfer..."
export FREESURFER_HOME=/home/pmahon/research/INN/software/freesurfer/7.4.1
source $FREESURFER_HOME/SetUpFreeSurfer.sh

echo "Pipeline Repository:      $1" 
echo "Subject Directory:        $2"
#singularity exec --bind $FREESURFER_HOME:$FREESURFER_HOME --bind /home:/home --bind /project:/project --bind /scratch:/scratch --bind /localscratch:/localscratch "$PIPELINE_ENVIRONMENT" ./batch_scripts/run_pipeline_rest_beamformer.sh

python "$PIPELINE_REPO" "$SUBJECT_DIRECTORY" 
