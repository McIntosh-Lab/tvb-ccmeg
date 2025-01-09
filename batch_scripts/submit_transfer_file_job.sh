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
# rsync -avzh --no-g --no-p --partial --progress $HOME/projects/def-rmcintos/Cam-CAN/mri/raw $(pwd)/_Data/mri/

# OR

# Copy the freesurfer data to scratch
rsync -avzh --no-g --no-p --partial --progress $HOME/projects/def-rmcintos/data-sets/Cam-CAN/MEG/freesurfer $(pwd)/_Data/mri/

rsync -avzh --no-g --no-p --partial --progress $HOME/projects/rpp-doesburg/databases/camcan872/cc700/meg/pipeline/release005/BIDSsep/derivatives_rest/aa/AA_nomovecomp/aamod_meg_maxfilt_00001 $(pwd)/_Data/meg/release005/BIDSsep/derivatives_rest/aa/AA_nomovecomp/aamod_meg_maxfilt_00001/

rsync -avzh --no-g --no-p --partial --progress $HOME/projects/rpp-doesburg/databases/camcan872/cc700/meg/pipeline/release004/BIDS_20190411/meg_emptyroom $(pwd)/_Data/meg/release004/BIDS_20190411/

rsync -avzh --no-g --no-p --partial --progress $HOME/projects/rpp-doesburg/databases/camcan_coreg/trans $(pwd)/_Data/meg/camcan_coreg/

