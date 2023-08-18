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

# Identify calibration and cross-talk files (important for Maxwell filtering)
calibration = '/home/sdobri/Software/CamCAN/tvb-ccmeg/tvb-ccmeg/sss_params/sss_cal.dat'
cross_talk = '/home/sdobri/Software/CamCAN/tvb-ccmeg/tvb-ccmeg/sss_params/ct_sparse.fif'

# Identify the files to process (only one subject for now)
raw_fname = '/home/sdobri/Documents/McLab/CamCAN/ccmeg/ccmeg_data/camCAN724/cc700/meg/pipeline/release005/BIDSsep/rest/sub-CC221954/ses-rest/meg/sub-CC221954_ses-rest_task-rest_meg.fif'
er_fname = '/home/sdobri/Documents/McLab/CamCAN/ccmeg/ccmeg_data/camCAN724/cc700/meg/pipeline/release005/BIDSsep/emptyroom/sub-CC221954/emptyroom/emptyroom_CC221954.fif'
trans = '/home/sdobri/Documents/McLab/CamCAN/ccmeg/ccmeg_data/camcan_derivatives/trans-halifax/sub-CC221954-trans.fif'
subject = 'sub-CC221954'
fs_dir = '/home/sdobri/Documents/McLab/CamCAN/ccmeg/ccmeg_data/camcan_derivatives/freesurfer/'

# We want to save output at various points in the pipeline
output_dir = '/home/sdobri/Documents/McLab/CamCAN/pipeline_test_output/'

#Preprocessing:

# Generate MNE Python report to visually inspect preprocessing steps
report = mne.Report(title='Test Subj', raw_psd=True)

# Read resting-state data
raw = preprocess.read_data(raw_fname)
raw.del_proj()                          # Don't want existing projectors, could add to preprocess.read_data() if we never want them
# Add raw data to report
report.add_raw(raw=raw, title='Raw')

# Compute head position throughout recording
head_pos = preprocess.compute_head_position(raw)
# Write head position to file (takes a while to compute)
# Add visualization of head motion to report
mne.chpi.write_head_pos(output_dir + 'head_pos.pos', head_pos)
report.add_figure(fig=mne.viz.plot_head_positions(head_pos, mode='traces', show=False),title='Head Motion')

# Apply Maxwell filtering with head motion correction
raw = preprocess.maxwell_filter(raw, head_pos, calibration, cross_talk)
# Add Maxwell filtered PSD to report
report.add_figure(fig=raw.compute_psd(fmax=350).plot(show=False), title='Maxwell Filtered')

# Filter data to remove line noise, slow drifts, and frequencies too high to be of interest
raw = preprocess.filter_data(raw)
# Add filtered PSD to report
report.add_figure(fig=raw.compute_psd(fmax=350).plot(show=False), title='Filtered')

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

# Save preprocessed MEG data
raw.save(output_dir + 'test_preprocessed.fif', overwrite=True)

# Save report
report.save(output_dir + 'report.html', overwrite=True)

# Calculate noise covariance from empty room data (need this for MNE)
noise_cov = preprocess.compute_noise_cov(er_fname, raw, calibration, cross_talk)
# Write noise covariance to file
mne.write_cov(output_dir + 'er-cov.fif', noise_cov, overwrite=True)

# Estimate source activity

# This section requires previously-computed boundary element model (BEM) surfaces to be in the FreeSurfer directory
# Setup source space
src = compute_source.setup_source_space(subject, fs_dir)
# Save source space
mne.write_source_spaces(output_dir + 'test_src.fif', src, overwrite=True)
# Make boundary element model (BEM)
bem = compute_source.make_bem(subject, fs_dir)
# Save BEM
mne.write_bem_solution(output_dir + 'test_bem.h5', bem, overwrite=True)

# Make inverse operator to go from sensor to source space
inverse_operator = compute_source.make_inverse_operator(raw, raw_fname, trans, src, bem, noise_cov)
# Save inverse operator
mne.minimum_norm.write_inverse_operator(output_dir + 'test_inv.fif', inverse_operator, overwrite=True)

# Estimate source activity
# Takes lots of memory so we should delete the objects we don't need
del report, head_pos, ecg_epochs, ecg_before, ecg_after, eog_epochs, eog_before, eog_after, bem, noise_cov
stc = compute_source.compute_inverse_solution_rest(raw, inverse_operator)
# Write source activity to file
for index, s in enumerate(stc):
    s.save(output_dir + 'stc/' + 'stc_test_' + str(index), overwrite=True)

# Estimate source activity in parcellated brain

# Read labels from parcellation file
labels = mne.read_labels_from_annot(subject, parc='Schaefer2018_200Parcels_17Networks_order', subjects_dir=fs_dir)
# Extract timeseries for parcellation ('mean_flip' option reduces cancellation due to differing source orientations)
parc_ts = mne.extract_label_time_course(stc, labels, src, mode='mean_flip')
np.save(output_dir + 'parc_ts_test', parc_ts)
