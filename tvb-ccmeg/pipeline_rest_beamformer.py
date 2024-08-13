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
#import nibabel		# Need this for legacy mne on cedar
import sklearn		# Need this for the fastica option in artifact rejection
import picard		# Need this for the picard option in artifact rejection
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
calibration = '/home/jsolomon/scratch/cam-Can/tvb-ccmeg/tvb-ccmeg/sss_params/sss_cal.dat'
cross_talk = '/home/jsolomon/scratch/cam-Can/tvb-ccmeg/tvb-ccmeg/sss_params/ct_sparse.fif'

# Identify the files to process
rest_raw_dname = '/home/jsolomon/projects/rpp-doesburg/databases/camcan872/cc700/meg/pipeline/release005/BIDSsep/derivatives_rest/aa/AA_nomovecomp/aamod_meg_maxfilt_00001/'
er_dname = '/home/jsolomon/projects/rpp-doesburg/databases/camcan872/cc700/meg/pipeline/release004/BIDS_20190411/meg_emptyroom/'
trans_dname = '/home/jsolomon/projects/rpp-doesburg/databases/camcan_coreg/trans/'
fs_dir = '/home/jsolomon/scratch/cam-Can/freesurfer/'
raw_fname = rest_raw_dname + subject + '/mf2pt2_' + subject + '_ses-rest_task-rest_meg.fif'
er_fname = er_dname + subject + '/emptyroom/emptyroom_' + subject[4:] + '.fif'
trans = trans_dname + subject + '-trans.fif'

# We want to save output at various points in the pipeline
output_dir = './processed_meg/' + subject + '/'
if not os.path.isdir(output_dir):
	os.mkdir(output_dir)

# Read resting-state data
raw = preprocess.read_data(raw_fname)
raw.crop(tmin=30, tmax=390)
raw.del_proj()                          # Don't want existing projectors, could add to preprocess.read_data() if we never want them
raw.pick(['meg', 'eog', 'ecg'])

# Filter data to remove line noise, slow drifts, and frequencies too high to be of interest
l_freq = 1.0    # High pass frequency in Hz
h_freq = 90     # Low pass frequency in Hz
raw = preprocess.filter_data(raw,l_freq=l_freq,h_freq=h_freq)

# Remove heartbeat and eye movement artifacts
pick_meg = mne.pick_types(raw.info, meg=True, eeg=False, stim=False, ref_meg=False)
raw, ica = preprocess.do_ICA(raw, picks=pick_meg, method = "picard")

# Downsample raw data to speed up computation
new_sfreq = 500
raw.resample(new_sfreq)

# Compute data covariance from two minutes of raw recording
data_cov = mne.compute_raw_covariance(raw, tmin=30, tmax=150)

# Compute noise covariance from empty room recording
er_raw = preprocess.read_data(er_fname)
er_raw.del_proj()
er_raw.pick(['meg'])	# I realize that this doesn' make sense
er_raw = preprocess.filter_data(er_raw,l_freq=l_freq,h_freq=h_freq)
ica.apply(er_raw)
er_raw.resample(new_sfreq)
noise_cov = mne.compute_raw_covariance(er_raw)

# Make boundary element model (BEM) surfaces if there isn't already a file
#if not os.path.isfile(fs_dir + '/' + subject + '/bem/watershed/' + subject + '-meg-bem.fif'):
#    mne.bem.make_watershed_bem(subject, subjects_dir=fs_dir, overwrite=True)

# This section requires previously-computed BEM surfaces to be in the FreeSurfer directory

# Set up forward solution
bem = compute_source.make_bem(subject, fs_dir)
src = mne.setup_volume_source_space(subject=subject, subjects_dir=fs_dir, bem=bem)
fwd = mne.make_forward_solution(raw.info, trans=trans, src=src, bem=bem, meg=True, eeg=False, mindist=5.0, n_jobs=None)
src.save(output_dir + 'src_beamformer-src.fif', overwrite=True)

# Compute the spatial filter
filts = mne.beamformer.make_lcmv(raw.info, fwd, data_cov, reg=0.05, noise_cov=noise_cov, pick_ori='max-power', weight_norm='unit-noise-gain', rank='info')

# Apply beamformer
start, stop = raw.time_as_index([30, 330])
stc = mne.beamformer.apply_lcmv_raw(raw, filts, start=start, stop=stop)
#stc.save(output_dir + 'stc_beamformer', overwrite=True)

# Extract timeseries for parcellated brain regions
labels_lh = fs_dir+subject+'/label/lh.Schaefer2018_200Parcels_17Networks_order.mgz'
labels_rh = fs_dir+subject+'/label/rh.Schaefer2018_200Parcels_17Networks_order.mgz'
labels_bh = fs_dir+subject+'/label/Schaefer2018_200Parcels_17Networks_order.mgz'
parc_ts_lh = mne.extract_label_time_course(stc, labels_lh, src, mode='auto')
parc_ts_rh = mne.extract_label_time_course(stc, labels_rh, src, mode='auto')
parc_ts_bh = mne.extract_label_time_course(stc, labels_bh, src, mode='auto')
np.save(output_dir + 'parc_ts_beamformer_lh', parc_ts_lh)
np.save(output_dir + 'parc_ts_beamformer_rh', parc_ts_rh)
np.save(output_dir + 'parc_ts_beamformer_bh', parc_ts_bh)

# Extract timeseries for aparc parcellated brain regions
labels_aparc = fs_dir+subject+'/mri/aparc+aseg.mgz'
parc_ts_aparc = mne.extract_label_time_course(stc, labels_aparc, src, mode='auto')
np.save(output_dir + 'parc_ts_beamformer_aparc', parc_ts_aparc)
