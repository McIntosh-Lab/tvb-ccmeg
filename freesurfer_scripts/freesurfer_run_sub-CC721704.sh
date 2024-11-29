#!/bin/bash
#SBATCH --time=24:00:00
#SBATCH --job-name=freesurfer-recon-sub-CC721704
#SBATCH --output=./logs/freesurfer/output/recon-sub-CC721704.out
#SBATCH --error=./logs/freesurfer/error/recon-sub-CC721704.err
#SBATCH --mem=8G
#SBATCH --account=rrg-rmcintos

#This script must be run after "./freesurfer_scripts/freesurfer_script.sh".

#Load FreeSurfer
export FREESURFER_HOME=/home/pmahon/research/INN/software/freesurfer/7.4.1
source $FREESURFER_HOME/SetUpFreeSurfer.sh

#Define output directory
SUBJECTS_DIR="$(pwd)/_Data/freesurfer"

#Run altered command for sub-CC721704
recon-all -skullstrip -wsthresh 15 -clean-bm -no-wsgcaatlas -subjid sub-CC721704recon-all -autorecon2 -autorecon3 -subjid sub-CC721704
