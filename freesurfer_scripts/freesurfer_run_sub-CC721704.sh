#!/bin/bash
#SBATCH --time=24:00:00
#SBATCH --job-name=freesurfer-recon-sub-CC721704
#SBATCH --output=./logs/recon_out/recon-sub-CC721704.out
#SBATCH --error=./logs/recon_err/recon-sub-CC721704.err
#SBATCH --mem=8000M
#SBATCH --account=rrg-rmcintos
export FREESURFER_HOME=/home/pmahon/research/INN/software/freesurfer/7.4.1
source $FREESURFER_HOME/SetUpFreeSurfer.sh
SUBJECTS_DIR='/home/jsolomon/scratch/cam-Can/freesurfer'
recon-all -skullstrip -wsthresh 15 -clean-bm -no-wsgcaatlas -subjid sub-CC721704recon-all -autorecon2 -autorecon3 -subjid sub-CC721704
