#!/bin/bash
# Set up free surfer
echo "Setting up FreeSurfer..."
export FREESURFER_HOME=/home/pmahon/research/INN/software/freesurfer/7.4.1
source $FREESURFER_HOME/SetUpFreeSurfer.sh
. /opt/miniconda3/bin/activate mne
# Run pipeline
python $HOME/projects/ctb-rmcintos/data-sets/Cam-CAN/tvb-ccmeg/tvb-ccmeg/pipeline_rest_beamformer.py $SUBJECT_DIRECTORY 
