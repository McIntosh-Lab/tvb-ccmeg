#!/bin/env python
#
# Module name: beamformer_test.py
#
# Description: Script to test pipeline for TVB Cam-CAN MEG
#
# Author: Simon Dobri <simon_dobri@sfu.ca>
#
# License: BSD (3-clause)

import mne              # Need MNE Python
import preprocess       # Module with all the preprocessing functions
import compute_source   # Module with functions to go from sensor space to source space
import numpy as np      # Need for array operations
import os
import sys
# IF the MNE wheel on cedar is used, then sklearn, nibabel and python-picard also need to be imported

# Check if a subject is passed

if len(sys.argv) <= 1:
    raise ValueError("A subject directory has not been provided. Usage:"
                     "\n\tpython pipeline_rest_beamformer.py <subject_name>")
else:
    subject = sys.argv[1]

# Set number of cores for parallel processing (must be done before running any linear algebra functions)
num_cpu = '16'
os.environ['OMP_NUM_THREADS'] = num_cpu

# Get paths to files
data_dir = os.path.abspath('./_Data')  # Parent directory

# Identify calibration and cross-talk files (important for Maxwell filtering)
calibration = os.path.join(os.path.abspath('.'), 'tvb-ccmeg/sss_params/sss_cal.dat')
cross_talk = os.path.join(os.path.abspath('.'), 'tvb-ccmeg/sss_params/ct_sparse.fif')

# Identify the files to process
# Raw data should be in a directory called 'meg' with the same parent directory as the pipeline code
meg_dir = os.path.join(data_dir,'meg/release005/BIDSsep')  # Directory containing MEG data
rest_raw_dname = os.path.join(meg_dir, 'rest')
er_dname = os.path.join(meg_dir, 'meg_emptyroom')
trans_dname = os.path.join(meg_dir, 'trans-halifax')
raw_fname = os.path.join(rest_raw_dname, subject, 'ses-rest/meg', subject + '_ses-rest_task-rest_meg.fif')
er_fname = os.path.join(er_dname, subject, 'emptyroom/emptyroom_' + subject[4:] + '.fif')
trans = os.path.join(trans_dname, subject + '-trans.fif')
# FreeSurfer outputs should be in a directory called 'freesurfer' with same parent directory as the pipeline code
fs_dir = os.path.join(data_dir,'mri/freesurfer')

# We want to save output at various points in the pipeline
output_dir = os.path.join(data_dir, 'processed_meg',subject)
if not os.path.isdir(output_dir):
	os.mkdir(output_dir)

# Set ECG / EOG correction method (options are ICA and SSP, the default is ICA)

ICA = True

# Pick either volumetric or surface mesh beamformers (default is volumetric)

Vol = True

# Read resting-state data
raw = preprocess.read_data(raw_fname)
raw.crop(tmin=30, tmax=390)
raw.del_proj()                          # Don't want existing projectors, could add to preprocess.read_data() if we never want them
if ICA:
	raw.pick(['meg', 'eog', 'ecg'])
else:
	raw.pick(['grad', 'eog', 'ecg'])

# Filter data to remove line noise, slow drifts, and frequencies too high to be of interest
l_freq = 1.0    # High pass frequency in Hz
h_freq = 90     # Low pass frequency in Hz
raw = preprocess.filter_data(raw,l_freq=l_freq,h_freq=h_freq)

# Remove heartbeat and eye movement artifacts
if ICA:
	pick_meg = mne.pick_types(raw.info, meg=True, eeg=False, stim=False, ref_meg=False)
	raw, ica = preprocess.do_ICA(raw, picks=pick_meg, method = "picard")
else:
	raw = preprocess.add_ecg_projectors(raw)
	raw = preprocess.add_eog_projectors(raw)

# Downsample raw data to speed up computation
new_sfreq = 500
raw.resample(new_sfreq)

# Save processed Raw data

raw.save(os.path.join(output_dir, 'sensor_processed_meg.fif'), overwrite=True)

# Compute data covariance from two minutes of raw recording
if ICA:
	raw.pick('grad')

data_cov = mne.compute_raw_covariance(raw, tmin=30, tmax=150)

# Compute noise covariance from empty room recording
er_raw = preprocess.read_data(er_fname)
er_raw.del_proj()
if ICA:
	er_raw.pick(['meg'])	# I realize that this doesn' make sense but I need the mags for the ICA
else:
	er_raw.pick(['grad'])

er_raw = preprocess.filter_data(er_raw,l_freq=l_freq,h_freq=h_freq)
if ICA:
	ica.apply(er_raw)
else:
	er_raw.add_proj(raw.info['projs'])
	er_raw.apply_proj()

er_raw.resample(new_sfreq)
if ICA:
	er_raw.pick(['grad'])

noise_cov = mne.compute_raw_covariance(er_raw)

# Make boundary element model (BEM) surfaces if there isn't already a file
if not os.path.isfile(fs_dir + '/' + subject + '/bem/watershed/' + subject + '-meg-bem.fif'):
    mne.bem.make_watershed_bem(subject, subjects_dir=fs_dir, overwrite=True)

# This section requires previously-computed BEM surfaces to be in the FreeSurfer directory
# Set up forward solution
bem = compute_source.make_bem(subject, fs_dir)

if Vol:
	src = mne.setup_volume_source_space(subject=subject, subjects_dir=fs_dir, bem=bem)
else:
	src = mne.setup_source_space(subject, subjects_dir=fs_dir) 

fwd = mne.make_forward_solution(raw.info, trans=trans, src=src, bem=bem, meg=True, eeg=False, mindist=5.0, n_jobs=None)
src.save(os.path.join(output_dir, 'src_beamformer-src.fif'), overwrite=True)

# Compute the spatial filter
filts = mne.beamformer.make_lcmv(raw.info, fwd, data_cov, reg=0.05, noise_cov=None, pick_ori='max-power', weight_norm='unit-noise-gain', rank='info')

# pick_ori=None, weight_norm=None, depth=None, rank=None) #Vasily's settings

# Apply beamformer
start, stop = raw.time_as_index([30, 390])
stc = mne.beamformer.apply_lcmv_raw(raw, filts, start=start, stop=stop)
stc.save(os.path.join(output_dir, 'stc_beamformer'), overwrite=True)

# Extract timeseries for aparc parcellated brain regions (volumetric)
# labels_aparc = fs_dir+subject+'/mri/aparc+aseg.mgz' # Volumetric
# parc_ts_aparc = mne.extract_label_time_course(stc, labels_aparc, src, mode='auto')
# np.save(output_dir + 'parc_ts_beamformer_aparc', parc_ts_aparc)

# Read labels from parcellation files and save to text files
# Aparc (FreeSurfer default)
labels_aparc = mne.read_labels_from_annot(subject, parc='aparc', subjects_dir=fs_dir)
with open(os.path.join(output_dir, 'aparc_labels.txt'),'w') as outfile:
    outfile.write('\n'.join(str(lab.name) for lab in labels_aparc))
# Schaefer
labels_schaefer = mne.read_labels_from_annot(subject, parc='Schaefer2018_200Parcels_17Networks_order', subjects_dir=fs_dir)
with open(os.path.join(output_dir, 'Schaefer_labels.txt'),'w') as outfile:
    outfile.write('\n'.join(str(lab.name) for lab in labels_schaefer))

# Extract timeseries for parcellations (surface mesh)
# Aparc
aparc_ts = mne.extract_label_time_course(stc, labels_aparc, src, mode='mean_flip')
np.save(os.path.join(output_dir, 'parc_ts_beamformer_aparc'), aparc_ts)
# Schaefer
schaefer_ts = mne.extract_label_time_course(stc, labels_schaefer, src, mode='mean_flip')
np.save(os.path.join(output_dir, 'parc_ts_beamformer_Schaefer'), schaefer_ts)
