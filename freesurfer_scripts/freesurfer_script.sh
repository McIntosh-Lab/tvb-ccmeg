#!/bin/bash
#SBATCH --array=0-653
#SBATCH --time=24:00:00
#SBATCH --job-name=freesurfer-recon
#SBATCH --output=./logs/freesurfer/output/recon-%A_%a.out
#SBATCH --error=./logs/freesurfer/error/recon-%A_%a.err
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --account=rrg-rmcintos

#Load Freesurfer
export FREESURFER_HOME=/home/pmahon/research/INN/software/freesurfer/7.4.1
source $FREESURFER_HOME/SetUpFreeSurfer.sh

shopt -s nullglob

#Define and create output directory
SUBJECTS_DIR="$(pwd)/_Data/mri/freesurfer/"

if [ ! -e "$(pwd)/_Data/mri/freesurfer" ]; then
  mkdir -p "$(pwd)/_Data/mri/freesurfer"
  echo "FreeSurfer directory created."
else
  echo "FreeSurfer directory already exists."
fi

#Define input directory
rawdir="$(pwd)/_Data/mri/raw/"
cd $rawdir

#Define current subject and start job
subs=(sub*)
subc=${subs[$SLURM_ARRAY_TASK_ID]}

echo "Starting subject $subc"

recon-all -subjid $subc -i "$rawdir"$subc"/rawdata/anat/"$subc"_T1w.nii.gz" -all
