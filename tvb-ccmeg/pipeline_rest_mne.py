#!/bin/env python
#
# Module name: pipeline_test.py
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

# Check if a subject is passed

if len(sys.argv) <= 1:
    raise ValueError("A subject directory has not been provided. Usage:"
                     "\n\tpython pipeline_test.py <subject_directory_name>")
else:
    subject = sys.argv[1]

# Set number of cores for parallel processing (must be done before running any linear algebra functions)
num_cpu = '16'
os.environ['OMP_NUM_THREADS'] = num_cpu

# Identify user's home directory
home_dir = os.path.expanduser('~')

# Identify calibration and cross-talk files (important for Maxwell filtering)
calibration = os.path.join(home_dir, 'projects/ctb-rmcintos/data-sets/Cam-CAN/tvb-ccmeg/tvb-ccmeg/sss_params/sss_cal.dat')
cross_talk = os.path.join(home_dir, 'projects/ctb-rmcintos/data-sets/Cam-CAN/tvb-ccmeg/tvb-ccmeg/sss_params/ct_sparse.fif')

# Identify the files to process
# Identify calibration and cross-talk files (important for Maxwell filtering)
calibration = '/home/sdobri/projects/ctb-rmcintos/data-sets/Cam-CAN/tvb-ccmeg/tvb-ccmeg/sss_params/sss_cal.dat'
cross_talk = '/home/sdobri/projects/ctb-rmcintos/data-sets/Cam-CAN/tvb-ccmeg/tvb-ccmeg/sss_params/ct_sparse.fif'

# Identify the files to process
rest_raw_dname = '/home/sdobri/projects/rpp-doesburg/databases/camcan872/cc700/meg/pipeline/release005/BIDSsep/derivatives_rest/aa/AA_nomovecomp/aamod_meg_maxfilt_00001/'
er_dname = '/home/sdobri/projects/rpp-doesburg/databases/camcan872/cc700/meg/pipeline/release004/BIDS_20190411/meg_emptyroom/'
trans_dname = '/home/sdobri/projects/rpp-doesburg/databases/camcan_coreg/trans/'
fs_dir = '/home/sdobri/projects/ctb-rmcintos/data-sets/Cam-CAN/freesurfer/'
raw_fname = rest_raw_dname + subject + '/mf2pt2_' + subject + '_ses-rest_task-rest_meg.fif'
er_fname = er_dname + subject + '/emptyroom/emptyroom_' + subject[4:] + '.fif'
trans = trans_dname + subject + '-trans.fif'


# We want to save output at various points in the pipeline
output_dir = '/home/sdobri/scratch/Cam-CAN/pipeline_test_output/' + subject + '/'
if not os.path.isdir(output_dir):
	os.mkdir(output_dir)

# Preprocessing:

# Generate MNE Python report for visual quality control
report = mne.Report(title=subject+'_QC_report', raw_psd=True)

# Read resting-state data
raw = preprocess.read_data(raw_fname)
raw.pick(['grad', 'eog', 'ecg'])                      # Discard magnetometer data, it's too noisy
raw.del_proj()                          # Don't want existing projectors, could add to preprocess.read_data() if we never want them
# Add raw data to report
report.add_raw(raw=raw, title='Raw')



# Filter data to remove line noise, slow drifts, and frequencies too high to be of interest
l_freq = 1.0    # High pass frequency in Hz
h_freq = 90     # Low pass frequency in Hz
raw = preprocess.filter_data(raw,l_freq=l_freq,h_freq=h_freq)

# Remove heartbeat artifacts
# Currently uses SSP, might be better (but slower) with ICA
# Define epochs based on heartbeat artifacts
ecg_epochs = mne.preprocessing.create_ecg_epochs(raw)
# Add plot of artifacts to report
ecg_before = ecg_epochs.average().apply_baseline(baseline=(None, -0.2))
report.add_evokeds(evokeds=ecg_before, titles='ECG Before')
# Calculate and add ECG projectors
raw = preprocess.add_ecg_projectors(raw)
# Add plot of corrected ECG epochs to report
ecg_after = mne.Epochs(raw, ecg_epochs.events, tmin=-0.5, tmax=0.5)
ecg_after = ecg_after.average().apply_baseline(baseline=(None, -0.2))
report.add_evokeds(evokeds=ecg_after, titles='ECG After')

# Remove ocular artifacts
# Currently uses SSP, might be better (but slower) with ICA
# Define epochs based on ocular artifacts
eog_epochs = mne.preprocessing.create_eog_epochs(raw)
# Add plot of artifacts to report
eog_before = eog_epochs.average().apply_baseline(baseline=(None, -0.2))
report.add_evokeds(evokeds=eog_before, titles='EOG Before')
# Calculate and add EOG projectors
raw = preprocess.add_eog_projectors(raw)
# Add plot of corrected EOG epochs to report
eog_after = mne.Epochs(raw, eog_epochs.events, tmin=-0.5, tmax=0.5)
eog_after = eog_after.average().apply_baseline(baseline=(None, -0.2))
report.add_evokeds(evokeds=eog_after, titles='EOG After')

# Downsample raw data to speed up computation
new_sfreq = 500
raw.resample(new_sfreq)

# Save preprocessed MEG data
raw.save(os.path.join(output_dir, 'test_preprocessed.fif'), overwrite=True)

# Save report
report.save(os.path.join(output_dir, 'report.html'), overwrite=True)

# Calculate noise covariance from empty room data (need this for MNE)
noise_cov = preprocess.compute_noise_cov(er_fname, raw, calibration, cross_talk)
# Write noise covariance to file
mne.write_cov(os.path.join(output_dir, 'er-cov.fif'), noise_cov, overwrite=True)

# Estimate source activity

# Make boundary element model (BEM) surfaces if there isn't already a file
if not os.path.isfile(os.path.join(fs_dir, subject, 'bem/watershed', subject + '-meg-bem.fif')):
    mne.bem.make_watershed_bem(subject, subjects_dir=fs_dir, overwrite=True)

# This section requires previously-computed BEM surfaces to be in the FreeSurfer directory
# Setup source space
src = compute_source.setup_source_space(subject, fs_dir)
# Save source space
mne.write_source_spaces(os.path.join(output_dir, 'test_src.fif'), src, overwrite=True)
# Make boundary element model (BEM)
bem = compute_source.make_bem(subject, fs_dir)
# Save BEM
mne.write_bem_solution(os.path.join(output_dir, 'test_bem.h5'), bem, overwrite=True)

# Make inverse operator to go from sensor to source space
inverse_operator = compute_source.make_inverse_operator(raw, raw_fname, trans, src, bem, noise_cov)
# Save inverse operator
mne.minimum_norm.write_inverse_operator(os.path.join(output_dir, 'test_inv.fif'), inverse_operator, overwrite=True)

# Estimate source activity
# First downsample to 500 Hz to avoid running out of memory when computing full source reconstruction
# raw.resample(500)

stc = compute_source.compute_inverse_solution_rest(raw, inverse_operator)

#   Write source activity to file
# stc.save(os.pathn.join(output_dir, 'stc_test'), overwrite=True)

# Estimate source activity in parcellated brain

# Read labels from parcellation file
labels = mne.read_labels_from_annot(subject, parc='Schaefer2018_200Parcels_17Networks_order', subjects_dir=fs_dir)
# Extract timeseries for parcellation ('mean' option avoids cancellation from default 'mean_flip' since MNE source activity is not signed)
parc_ts = mne.extract_label_time_course(stc, labels, src, mode='mean')
# Save parcellated time series to file
np.save(os.path.join(output_dir, 'parc_ts_mne'), parc_ts)
