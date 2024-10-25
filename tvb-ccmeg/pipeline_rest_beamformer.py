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

# Check if a subject is passed

if len(sys.argv) <= 1:
    raise ValueError("A subject directory has not been provided. Usage:"
                     "\n\tpython beamformer_test.py <subject_name>")
else:
    subject = sys.argv[1]

# Set number of cores for parallel processing (must be done before running any linear algebra functions)
num_cpu = '16'
os.environ['OMP_NUM_THREADS'] = num_cpu

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

# Read resting-state data
raw = preprocess.read_data(raw_fname)
raw.del_proj()                          # Don't want existing projectors, could add to preprocess.read_data() if we never want them
raw.pick(['grad', 'eog', 'ecg'])                      # Discard magnetometer data, it's too noisy

# Filter data to remove line noise, slow drifts, and frequencies too high to be of interest
l_freq = 1.0    # High pass frequency in Hz
h_freq = 90     # Low pass frequency in Hz
raw = preprocess.filter_data(raw,l_freq=l_freq,h_freq=h_freq)

# Remove heartbeat and eye movement artifacts
#raw = preprocess.add_ecg_projectors(raw)
#raw = preprocess.add_eog_projectors(raw)
ica = preprocess.compute_ica(raw)
raw = preprocess.remove_eog_ecg(ica, raw)

# Downsample raw data to speed up computation
new_sfreq = 500
raw.resample(new_sfreq)

# Compute data covariance from two minutes of raw recording
data_cov = mne.compute_raw_covariance(raw, tmin=30, tmax=150)

# Compute noise covariance from empty room recording
#er_raw = preprocess.read_data(er_fname)
#er_raw.del_proj()
#er_raw.pick(['grad'])
#er_raw = preprocess.filter_data(er_raw,l_freq=l_freq,h_freq=h_freq)
#er_raw.add_proj(raw.info['projs'])
#er_raw.apply_proj()
#er_raw.resample(new_sfreq)
#noise_cov = mne.compute_raw_covariance(er_raw)

# Make boundary element model (BEM) surfaces if there isn't already a file
if not os.path.isfile(fs_dir + '/' + subject + '/bem/watershed/' + subject + '-meg-bem.fif'):
    mne.bem.make_watershed_bem(subject, subjects_dir=fs_dir, overwrite=True)

# This section requires previously-computed BEM surfaces to be in the FreeSurfer directory

# Set up forward solution
bem = compute_source.make_bem(subject, fs_dir)
#src = mne.setup_volume_source_space(subject=subject, subjects_dir=fs_dir, bem=bem)
src = mne.setup_source_space(subject, subjects_dir=fs_dir)
fwd = mne.make_forward_solution(raw.info, trans=trans, src=src, bem=bem, meg=True, eeg=False, mindist=5.0, n_jobs=None)
#src.save(output_dir + 'src_beamformer-src.fif', overwrite=True)

# Compute the spatial filter
filts = mne.beamformer.make_lcmv(raw.info, fwd, data_cov, reg=0.05, noise_cov=None, pick_ori='max-power', weight_norm='unit-noise-gain', rank='info')

# Apply beamformer
start, stop = raw.time_as_index([30, 330])
stc = mne.beamformer.apply_lcmv_raw(raw, filts, start=start, stop=stop)
#stc.save(output_dir + 'stc_beamformer', overwrite=True)

# Extract timeseries for aparc parcellated brain regions (volumetric)
#labels_aparc = fs_dir+subject+'/mri/aparc+aseg.mgz'
#parc_ts_aparc = mne.extract_label_time_course(stc, labels_aparc, src, mode='auto')

# Read labels from parcellation files and save to text files
# Aparc (FreeSurfer default)
labels_aparc = mne.read_labels_from_annot(subject, parc='aparc', subjects_dir=fs_dir)
with open(os.path.join(output_dir, 'aparc_labels.txt'),'w') as outfile:
    outfile.write('\n'.join(str(lab.name) for lab in labels_aparc))
# Schaefer
labels_schaefer = mne.read_labels_from_annot(subject, parc='Schaefer2018_200Parcels_17Networks_order', subjects_dir=fs_dir)
with open(os.path.join(output_dir, 'Schaefer_labels.txt'),'w') as outfile:
    outfile.write('\n'.join(str(lab.name) for lab in labels_schaefer))

# Extract timeseries for parcellations
# Aparc
aparc_ts = mne.extract_label_time_course(stc, labels_aparc, src, mode='mean_flip')
np.save(output_dir + 'parc_ts_beamformer_aparc', aparc_ts)
# Schaefer
schaefer_ts = mne.extract_label_time_course(stc, labels_schaefer, src, mode='mean_flip')
np.save(output_dir + 'parc_ts_beamformer_Schaefer', schaefer_ts)
