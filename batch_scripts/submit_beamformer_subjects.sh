#!/bin/bash

# Author: Patrick Mahon
# Email: pmahon@sfu.ca
#
# submit_subjects.sh is used to process a list of subject directories using 
# the given processing pipeline and pipeline environment via the slurm workload 
# manager.
# 
# Arguments:
# 
#	pipeline_environment:	A apptainer/singularity image with the
#				necessary pipeline dependencies installed.
#
#	pipeline_repository: 	The directory containing the pipeline code base 
#				with a pipeline excectutable at the top level. 
#				See below for details.
#
# 	subject_list:	A text file with a list of subject directories, one per 
#			line.
#
# Usage:
# 	./submit_subjects.sh <pipeline_environment.sif> <pipeline_repository> <subject_list.txt>
#
# --------------------------------------------------------------------------- #
# Subject Directory Structure
# --------------------------------------------------------------------------- #
#
# The script should be called from the parent directory, or the directory 
# containing, the subject directories. The subject_list text file contains the
# names of the subjects/subject directories to be processed on each line. E.g.
# 
# <subject_list.txt>
# <BOF>
# subject_one
# subject_two
# subject_three
# <EOF>
#
# Where the directory structure is:
# 
# |- parent_directory
#    	|- subject_one
#	|- subject_two
#	|- subject_three
#
# --------------------------------------------------------------------------- #
# Pipeline Repository
# --------------------------------------------------------------------------- #
#
# The pipeline_repository is the code base for the processing pipeline. The top 
# level of the code base needs to contain a pipeline or pipeline_test
# excecutable that takes the subject_directory as it's only argument. E.g.
# 
# For a bash pipeline:
#
# 	./pipeline_repository/pipeline.sh <subject_directory>
#
# For a python pipeline:
#
#	python pipeline_repository/pipeline.py <subject_directory>
#
# etc...
#
# --------------------------------------------------------------------------- #
# Pipeline Environment
# --------------------------------------------------------------------------- #
#
# The pipeline_environment is a an apptainer/singularity image with all the 
# pipeline repo dependencies installed. 
#
#

#!/bin/bash

# Sourcing freesurfer
module load freesurfer
source $EBROOTFREESURFER/FreeSurferEnv.sh

# Rest of your script

SUBMIT_SUBJECT_SCRIPT_PATH="$HOME/projects/ctb-rmcintos/data-sets/Cam-CAN/tvb-ccmeg/batch_scripts/submit_beamformer_subject.sh"

# Check if a file name is provided as an argument
if [ $# -ne 3 ]; then
    echo "Usage: $0 <pipeline_environment.sif> <pipeline_repository> <subject_list.txt>"
    exit 1
fi

PIPELINE_ENVIRONMENT=$1
PIPELINE_REPO=$2
SUBJECT_LIST=$3


# Check if the file exists
if [ ! -f "$SUBJECT_LIST" ]; then
    echo "File not found: $SUBJECT_LIST"
    exit 1
fi

# Iterate over each line in the file
while IFS= read -r subject_name; do
    # Submit a Slurm job for each line
    sbatch -J $PIPELINE_REPO_$subject_name $SUBMIT_SUBJECT_SCRIPT_PATH $PIPELINE_ENVIRONMENT $PIPELINE_REPO $subject_name
done < "$SUBJECT_LIST"

