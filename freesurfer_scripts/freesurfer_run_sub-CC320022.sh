#!/bin/bash
#SBATCH --time=24:00:00
#SBATCH --job-name=freesurfer-recon-sub-CC320022
#SBATCH --output=./logs/freesurfer/output/recon-sub-CC320022.out
#SBATCH --error=./logs/freesurfer/error/recon-sub-CC320022.err
#SBATCH --mem=8G
#SBATCH --account=rrg-rmcintos

#This script must be run after "$(pwd)/freesurfer_scripts/freesurfer_script.sh".

#Load freesurfer
export FREESURFER_HOME=/home/pmahon/research/INN/software/freesurfer/7.4.1
source $FREESURFER_HOME/SetUpFreeSurfer.sh

#Define output directory
SUBJECTS_DIR="$(pwd)/_Data/mri/freesurfer"

#Run altered command for sub-CC320022

recon-all -skullstrip -gcut -clean-bm -subjid sub-CC320022

recon-all -autorecon2 -autorecon3 -subjid sub-CC320022
