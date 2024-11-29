# Cam_CAN_MEG_Resting_State_Pipeline

This repository contains a pipeline to clean and create source localized data for the resting state Cam-CAN MEG dataset. This pipeline was created by Dr. Simon Dobri and developed by Dr. Simon Dobri and Dr. Jack Solomon.

## Repository Outline

This repository contains code that:
- Uses freesurfer to create parcellated structural MRI data
- extracts window of resting state data and cleans it using a bandpass and notch filter as well as either SSP or ICA motion correction.
- Projects data from sensor to source space using either a volumetric
  - Optionally parcellates the source level data

## Dependencies

The dependencies for this analysis are as follows. 

- mne (latest)
  - If using the cedar preinstalled mne wheel the additional dependencies are:
    - nibabel (latest)
    - sklearn (latest)
    - python-picard (latest)
   
Dependencies have been loaded in an apptainer (written by Patrick Mahon), that can be located at `~/projects/def-rmcintos/data-sets/meg_environment.sif`.

The scripts were run in python 3.11.4 for publication. They may work with other versions of python and matlab but are not guaranteed to function correctly.

## Code Usage

### Raw data

To adhere to the [lab SOP](https://github.com/McIntosh-Lab/Standard-Operating-Procedures), data will need to be copied from the `~/projects/` directory into your `~/scratch`.

There are two directories needed to run the pipeline.
The raw MEG data is located in `~/projects/def-rmcintos/Cam-CAN/meg`. This directory contains:
  - The raw resting state MEG data for each participant
    - "**_ADD SECTION FOR DIFFERENT RAW DATA FORMATS WHEN NEEDED_**"
  - The emptyroom recordings for each participant
  - the transformation files

The raw structural MRI data is located in `~/projects/def-rmcintos/Cam-CAN/mri/raw/`. This directory contains:
  - The raw T1w data files for each participant
  - Optionally, the parcellations created by the freesurfer analysis are stored in `~/projects/def-rmcintos/data-sets/Cam-CAN/MEG/freesurfer/`

### Setting up the pipeline directory

This data needs to be moved into a `/_Data` directory inside of the pipelines parent directory.

To create the appropriate directory tree and copy both the apptainer file and the MEG raw data, use the following commands:

```
cd ~/scratch/
git clone <insert https URL>
cd tvb-ccmeg
cp ~/projects/def-rmcintos/data-sets/meg_environment.sif .
mkdir _Data
rsync -avzh --no-g --no-p --partial --progress /home/jsolomon/projects/def-rmcintos/Cam-CAN/meg ./_Data/
```

To copy the MRI data you can run either of the following code blocks:

- To copy the raw data and run the freesurfer scripts
```
#ADD LINES TO COPY MRI DATA AND SUBMIT MRI SCRIPTS IF WE DECIDE THAT IT THEY CANNOT BE POINTED AT ~/projects/
```
- To copy the parcellated outputs
```
rsync -avzh --no-g --no-p --partial --progress ~/projects/def-rmcintos/data-sets/Cam-CAN/MEG/freesurfer ./_Data/
```

### Running the pipeline

There are two booleans in `./tvb-ccmeg/pipeline_rest_beamformer.py` that should be considered prior to running the script that control the use of ICA vs. SSP for motion correction and surface mesh vs. volumetric beamformers. The defaults reflect the settings used to create the processed MEG data stored in "**_UPDATE PATH WHEN KNOWN_**".

Once the data is loaded, the pipeline can be run using the batch script `./batch_scripts/submit_beamformer_subjects.sh`.

To submit the job ensure that the working directory is the git repository's parent directory and use the following code:

```
./batch_scripts/submit_beamformer_subjects.sh meg_environment.sif ./tvb-ccmeg/pipeline_rest_beamformer.py ./batch_scripts/subject_list.txt
```

This will create the processed MEG data files in `./_Data/processed_meg/`.

