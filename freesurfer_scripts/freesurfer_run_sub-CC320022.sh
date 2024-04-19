#!/bin/bash
#SBATCH --time=24:00:00
#SBATCH --job-name=freesurfer-recon-sub-CC320022
#SBATCH --output=recon-sub-CC320022.out
#SBATCH --error=recon-sub-CC320022.err
#SBATCH --mem=8G
#SBATCH --account=rrg-rmcintos
FREESURFER_HOME='/home/pmahon/research/INN/software/freesurfer/7.4.1'
source $FREESURFER_HOME/SetUpFreeSurfer.sh
SUBJECTS_DIR='/home/sdobri/scratch/Cam-CAN/freesurfer'
recon-all -skullstrip -gcut -clean-bm -subjid sub-CC320022
recon-all -autorecon2 -autorecon3 -subjid sub-CC320022
