#!/bin/env python
#
# Module name: beamformer_test.py
#
# Description: Script to test pipeline for TVB Cam-CAN MEG
#
# Authors: Simon Dobri <simon_dobri@sfu.ca> & Jack Solomon <jack_solomon@sfu.ca> $ Santiago Flores <santiago_flores_alonso@sfu.ca>
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

### FILE I/O ###

# Get paths to files
data_dir = os.path.abspath('./_Data')  # Parent directory

# Identify calibration and cross-talk files (important for Maxwell filtering)
calibration = os.path.join(os.path.abspath('.'), 'tvb-ccmeg/sss_params/sss_cal.dat')
cross_talk = os.path.join(os.path.abspath('.'), 'tvb-ccmeg/sss_params/ct_sparse.fif')

# Identify the files to process
# Raw data should be in a directory called 'meg' with the same parent directory as the pipeline code

meg_dir = os.path.join(data_dir, 'meg')  # Directory containing MEG data
rest_raw_dname = os.path.join(meg_dir, 'meg_restingstate')
er_dname = os.path.join(meg_dir, 'meg_emptyroom')
trans_dname = os.path.join(meg_dir, 'camcan_coreg')
raw_fname = os.path.join(rest_raw_dname, subject, 'mf2pt2_' + subject + '_ses-rest_task-rest_meg.fif')
er_fname = os.path.join(er_dname, subject, 'emptyroom/emptyroom_' + subject[4:] + '.fif')
trans = os.path.join(trans_dname, subject + '-trans.fif')
# FreeSurfer outputs should be in a directory called 'freesurfer' with same parent directory as the pipeline code
fs_dir = os.path.join(data_dir,'mri/freesurfer')

# We want to save output at various points in the pipeline
output_dir = os.path.join(data_dir, 'processed_meg', subject)
if not os.path.isdir(output_dir):
	os.mkdir(output_dir)

### USER DEFINED VARIABLES ###

# Set ECG / EOG correction method (options are ICA and SSP, setting ICA to False uses SSP)
ICA = True

# Pick either volumetric or surface mesh beamformers (setting Vol to False uses surface mesh)
Vol = False

# Downsample boolean and default downsample factor
downsamp = True
downsamp_factor = 2

# Add / remove head position plot from QC report (if using Cam-CAN maxfiltered data this variable needs to be False)
plot_head_pos = False

# Define frequency bands of interest
bands = {
	'delta': (1, 4),
	'theta': (4, 7),
	'alpha': (8, 12),
	'beta': (15, 29),
	'g_low': (30, 59),
	'g_high': (60, 90)
}

### RUN PIPELINE ###

# Generate MNE Python report for visual quality control
report = mne.Report(title=subject+'_QC_report', raw_psd=True)

# Read resting-state data
raw = preprocess.read_data(raw_fname)
raw.crop(tmin=30, tmax=390)
raw.del_proj()                          # Don't want existing projectors, could add to preprocess.read_data() if we never want them

# Add raw data to report
report.add_raw(raw=raw, title='Raw')

# Compute head position throughout recording and add to report
if plot_head_pos:
	head_pos = preprocess.compute_head_position(raw)
	report.add_figure(fig=mne.viz.plot_head_positions(head_pos, mode='traces', show=False), title='Head Motion')

if ICA:
	raw.pick(['meg', 'eog', 'ecg'])
else:
	raw.pick(['grad', 'eog', 'ecg'])

# Filter data to remove line noise, slow drifts, and frequencies too high to be of interest
l_freq = 1.0    # High pass frequency in Hz
h_freq = 90     # Low pass frequency in Hz
raw = preprocess.filter_data(raw,l_freq=l_freq,h_freq=h_freq)

# Add filtered PSD to report
report.add_figure(fig=raw.compute_psd(fmax=350).plot(show=False), title='Filtered')

# Define epochs based on heartbeat artifacts
ecg_epochs = mne.preprocessing.create_ecg_epochs(raw)
ecg_before = ecg_epochs.average().apply_baseline(baseline=(None, -0.2))
# Add to report
report.add_evokeds(evokeds=ecg_before, titles='ECG Before')

# Define epochs based on ocular artifacts
eog_epochs = mne.preprocessing.create_eog_epochs(raw)
eog_before = eog_epochs.average().apply_baseline(baseline=(None, -0.2))
# Add plot of EOG artifacts to report
report.add_evokeds(evokeds=eog_before, titles='EOG Before')

# Remove heartbeat and eye movement artifacts
if ICA:
	pick_meg = mne.pick_types(raw.info, meg=True, eeg=False, stim=False, ref_meg=False)
	raw, ica = preprocess.do_ICA(raw, picks=pick_meg, method = "picard")
else:
	raw = preprocess.add_ecg_projectors(raw)
	raw = preprocess.add_eog_projectors(raw)

# Add plot of corrected ECG epochs to report
ecg_after = mne.Epochs(raw, ecg_epochs.events, tmin=-0.5, tmax=0.5)
ecg_after = ecg_after.average().apply_baseline(baseline=(None, -0.2))
report.add_evokeds(evokeds=ecg_after, titles='ECG After')

# Add plot of corrected EOG epochs to report
eog_after = mne.Epochs(raw, eog_epochs.events, tmin=-0.5, tmax=0.5)
eog_after = eog_after.average().apply_baseline(baseline=(None, -0.2))
report.add_evokeds(evokeds=eog_after, titles='EOG After')

# Downsample raw data to speed up computation
sfreq = raw.info['sfreq']

if downsamp:
	sfreq = int(sfreq / downsamp_factor)
	raw.resample(sfreq)

# Save processed Raw data

raw.save(os.path.join(output_dir, 'sensor_processed_meg.fif'), overwrite=True)

# Calculate normalized PSD
n_fft=1000
if downsamp:
	n_fft = int(n_fft/downsamp_factor)
sensor_ts_PSD, sensor_PSD_freq, sensor_power_bands = compute_source.PSD_per_timeseries(raw._data, bands, sfreq = sfreq, h_freq = h_freq, n_fft = n_fft)
np.save(os.path.join(output_dir, 'sensor_PSD'), sensor_ts_PSD)
np.save(os.path.join(output_dir, 'PSD_freq'), sensor_PSD_freq)

# Add filtered PSD to report
report.add_figure(fig=raw.compute_psd(method = 'welch', window = 'hann', fmin = 0, fmax=h_freq, n_fft = n_fft, n_overlap = n_fft // 2).plot(show = False), title = 'Filtered Artifact Removed')

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

# er_raw.resample(new_sfreq)
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
start, stop = raw.time_as_index([0, 390])
stc = mne.beamformer.apply_lcmv_raw(raw, filts, start=start, stop=stop)
stc.save(os.path.join(output_dir, 'stc_beamformer'), overwrite=True)

# Get PSDs from vertices
stc_ts_PSD, source_PSD_freq, stc_power_bands = compute_source.PSD_per_timeseries(stc.data, bands, sfreq = sfreq, h_freq = h_freq, n_fft = n_fft)
np.save(os.path.join(output_dir, 'stc_ts_PSD'), stc_ts_PSD)
np.save(os.path.join(output_dir, 'source_PSD_freq'), source_PSD_freq)

# Morph to fsAverage
stc_fsAvg = compute_source.morph_2_fsaverage(stc, fs_dir, subject)
stc_fsAvg.save(os.path.join(output_dir, 'stc_fsAverage_beamformer'), overwrite=True)

# Parcellate_Source_Data
labels_aparc, labels_schaefer, parc_ts_aparc, parc_ts_schaefer = compute_source.parcellate_source_data(src, stc, subject, fs_dir, output_dir, Vol, mode = 'pca_flip')

# Calculate Source PSD
aparc_ts_PSD, source_PSD_freq, aparc_power_bands = compute_source.PSD_per_timeseries(parc_ts_aparc, bands, sfreq = sfreq, h_freq = h_freq, n_fft = n_fft)
schaefer_ts_PSD, source_PSD_freq, schaefer_power_bands = compute_source.PSD_per_timeseries(parc_ts_schaefer, bands, sfreq = sfreq, h_freq = h_freq, n_fft = n_fft)
np.save(os.path.join(output_dir, 'parc_ts_beamformer_aparc_PSD'), aparc_ts_PSD)
np.save(os.path.join(output_dir, 'parc_ts_beamformer_schaefer_PSD'), schaefer_ts_PSD)
np.save(os.path.join(output_dir, 'source_PSD_freq'), source_PSD_freq)

# Save report
report.save(os.path.join(output_dir, 'report.html'), overwrite=True)
