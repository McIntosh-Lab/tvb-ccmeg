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

The scripts were run in python 3.11.4 for publication. They may work with other versions of python but are not guaranteed to function correctly.

## Code Usage

### Raw data

To adhere to the [lab SOP](https://github.com/McIntosh-Lab/Standard-Operating-Procedures), data will need to be copied from the `~/projects/` directory into your `~/scratch`.

There are two directories needed to run the pipeline.
The raw MEG data is located in `~/projects/def-rmcintos/Cam-CAN/meg`. This directory contains:
  - The raw resting state MEG data for each participant
    - "**_ADD SECTION FOR DIFFERENT RAW DATA FORMATS WHEN NEEDED_**"
  - The emptyroom recordings for each participant
  - the transformation files

The parcellations created by the FreeSurfer analysis are stored in `~/projects/def-rmcintos/data-sets/Cam-CAN/MEG/freesurfer/`. This contains:
  - The MRI parcellations created by the FreeSurfer
  - Optionally, the raw T1w data files for each participant are located in `~/projects/def-rmcintos/Cam-CAN/mri/raw/`.

### Setting up the pipeline directory

This data needs to be moved into a `/_Data` directory inside of the pipelines parent directory.

```
cd ~/scratch/
git clone <insert https URL>
cd tvb-ccmeg
```

Once inside the parent directory of the git repository, ALL of the following instructions are to be run from this directory. As the batch scripts require a specific directory structure

Use the following code block to create the appropriate directory structure and copy the apptainer file, the MEG raw data and the FreeSurfer parcellations:

```
cp ~/projects/def-rmcintos/data-sets/meg_environment.sif .
sbatch ./batch_scripts/submit_transfer_file_job.sh  
```

If you want to re-run the FreeSurfer analysis then uncomment line 20 of `./batch_scripts/submit_transfer_file_job.sh` and comment line 25. This will copy the raw MRI data and you will then need to run the FreeSurfer pipeline.

### Running the FreeSurfer pipeline (optional)
To run the FreeSurfer pipeline use the following code blocks:

```
sbatch ./freesurfer_scripts/freesurfer_script.sh
```

Once this job is completed then run:

```
sbatch ./freesurfer_scripts/freesurfer_run_sub-CC320022.sh
sbatch ./freesurfer_scripts/freesurfer_run_sub-CC721704.sh
```

### Running the pipeline

There are two booleans in `./tvb-ccmeg/pipeline_rest_beamformer.py` that should be considered prior to running the script that control the use of ICA vs. SSP for motion correction (line 57) and surface mesh vs. volumetric beamformers (line 61). The defaults reflect the settings used to create the processed MEG data stored in "**_UPDATE PATH WHEN KNOWN_**".

Once the data is loaded, the pipeline can be run using the batch script `./batch_scripts/submit_beamformer_subjects.sh`.

To submit the job ensure that the working directory is the git repository's parent directory and use the following code:

```
./batch_scripts/submit_beamformer_subjects.sh meg_environment.sif ./tvb-ccmeg/pipeline_rest_beamformer.py ./batch_scripts/subject_list.txt
```

This will create the processed MEG data files in `./_Data/processed_meg/`.
