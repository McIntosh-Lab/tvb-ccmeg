#!/bin/env python
#
# Module name: preprocess.py
#
# Description: functions used to preprocess Cam-CAN MEG data for pipeline
#
# Authors: Simon Dobri <simon_dobri@sfu.ca>
#
# License: BSD (3-clause)

import mne

def read_data(fname):
    #Read in MEG data in fif format
    raw = mne.io.read_raw_fif(fname, preload=True)  # Need to preload to filter
    #Fix channel labelling (may not be necessary depending on system, 
    # only has small effect anyways according to MNE-Python documentation)
    mne.channels.fix_mag_coil_types(raw.info)
    return raw

def compute_noise_cov(er_fname, raw):
    # Important to apply the same preprocessing steps to empty room recording as subject recording
    er_raw = read_data(er_fname)
    er_raw.del_proj()
    er_raw.info['bads'] = raw.info['bads']
    er_raw = mne.preprocessing.maxwell_filter(er_raw,coord_frame='meg') # Does it matter that we use a different coordinate frame? We can't really do this if we apply Maxwell filtering with head movement correction. 
    er_raw = filter_data(er_raw)
    er_raw.add_proj(raw.info['projs'])
    noise_cov = mne.compute_raw_covariance(er_raw, tmin=0, tmax=None)
    return noise_cov

def mark_bad_channels(raw):
    # Mark bad channels, necessary to avoid noise spreading in Maxwell filtering
    # Ideally, this would be done manually at the time of recording
    auto_noisy_chs, auto_flat_chs, auto_scores = mne.preprocessing.find_bad_channels_maxwell(raw, return_scores=True)
    bads = raw.info['bads'] + auto_noisy_chs + auto_flat_chs
    raw.info['bads'] = bads
    return raw

def compute_head_position(raw):
    # Compute head position indicator coil amplitudes (pretty slow)
    chpi_amplitudes = mne.chpi.compute_chpi_amplitudes(raw)
    # Compute head position indicator coil locations (pretty slow)
    chpi_locs = mne.chpi.compute_chpi_locs(raw.info, chpi_amplitudes)
    # Compute head position (much faster than the last two steps)
    head_pos = mne.chpi.compute_head_pos(raw.info, chpi_locs)
    return head_pos


def maxwell_filter(raw, head_pos):
    # Fine calibration file?
    # Crosstalk file?
    # Spatiotemporal or just spatial?
    # Detect bad channels, necessary to avoid noise spreading, ideally done manually
    raw = mark_bad_channels(raw)
    # Apply Maxwell filtering with head motion correction
    raw = mne.preprocessing.maxwell_filter(raw, head_pos=head_pos)
    return raw

def add_ecg_projectors(raw):
    ecg_proj, ecg_array = mne.preprocessing.compute_proj_ecg(raw) # Default options look fine
    raw.add_proj(ecg_proj)
    raw.apply_proj()
    return raw

def add_eog_projectors(raw):
    eog_proj, eog_array = mne.preprocessing.compute_proj_eog(raw) # Default options look fine
    raw.add_proj(eog_proj)
    raw.apply_proj()
    return raw

def compute_ica(raw):
    filt_raw = raw.copy().filter(l_freq=1.0, h_freq=None)   #Filter slow drift
    ica = mne.preprocessing.ICA(n_components=15, max_iter='auto')
    ica.fit(filt_raw)
    return ica

def remove_eog_ecg(ica, raw):
    eog_indices, eog_scores = ica.find_bads_eog(raw)
    ecg_indices, ecg_scores = ica.find_bads_ecg(raw)
    return eog_indices, ecg_indices

def filter_data(raw):
    meg_picks = mne.pick_types(raw.info, meg=True)  #Only filter MEG channels
    freqs = (50, 100)                               #50 Hz and its first harmonic (recorded in UK)
    raw.notch_filter(freqs=freqs, picks=meg_picks)  #Use a notch filter to take out power line noise
    raw.filter(l_freq=0.1, h_freq=100, picks=meg_picks) #Bandpass filter data (probably not any detectable high gamma activity in resting state because SNR is too low)
    return raw
