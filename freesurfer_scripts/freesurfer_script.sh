#!/bin/bash
#SBATCH --array=0-653
#SBATCH --time=24:00:00
#SBATCH --job-name=freesurfer-recon
#SBATCH --output=logs/recon_out/recon-%A_%a.out
#SBATCH --error=logs/recon_err/recon-%A_%a.err
#SBATCH --cpus-per-task=1
#SBATCH --mem=8000M
#SBATCH --account=rrg-rmcintos
export FREESURFER_HOME=/home/pmahon/research/INN/software/freesurfer/7.4.1
source $FREESURFER_HOME/SetUpFreeSurfer.sh
shopt -s nullglob
SUBJECTS_DIR='/home/jsolomon/scratch/cam-Can/freesurfer/'
rawdir='/home/jsolomon/projects/def-rmcintos/Cam-CAN/mri/raw/'
cd $rawdir
subs=(sub*)
subc=${subs[$SLURM_ARRAY_TASK_ID]}
echo "Starting subject $subc"
recon-all -subjid $subc -i "$rawdir"$subc"/rawdata/anat/"$subc"_T1w.nii.gz" -all
