#!/bin/bash
#SBATCH --output=./logs/copy_data/output/job_output_%j.out
#SBATCH --error=./logs/copy_data/error/job_error_%j.err
#SBATCH --ntasks=1
#SBATCH --time=24:00:00
#SBATCH --mem=64G
#SBATCH --account=rrg-rmcintos

if [ ! -e "$(pwd)/_Data/mri" ]; then
    mkdir -p "$(pwd)/_Data/mri"
    echo "Raw MRI directory created."
else
    echo "Raw MRI directory already created."
fi

# Copy MEG data to scratch
rsync -avzh --no-g --no-p --partial --progress $HOME/projects/def-rmcintos/Cam-CAN/meg $(pwd)/_Data/

# If you want to run freesurfer yourself copy the raw MRI data below
#rsync -avzh --no-g --no-p --partial --progress $HOME/projects/def-rmcintos/Cam-CAN/mri/raw $(pwd)/_Data/mri/

# OR

# Copy the freesurfer data to scratch
rsync -avzh --no-g --no-p --partial --progress $HOME/projects/def-rmcintos/data-sets/Cam-CAN/MEG/freesurfer $(pwd)/_Data/mri/
