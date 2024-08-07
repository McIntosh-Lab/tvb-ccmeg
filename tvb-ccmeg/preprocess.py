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

def compute_noise_cov(er_fname, raw, calibration, cross_talk):
    # Important to apply the same preprocessing steps to empty room recording as subject recording
    er_raw = read_data(er_fname)
    er_raw.del_proj()
    er_raw = mne.preprocessing.maxwell_filter_prepare_emptyroom(er_raw, raw=raw)
    er_raw = mne.preprocessing.maxwell_filter(er_raw, calibration=calibration, cross_talk=cross_talk) 
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


def maxwell_filter(raw, calibration, cross_talk, head_pos=None):
    # Fine calibration file?
    # Crosstalk file?
    # Spatiotemporal or just spatial?
    # Detect bad channels, necessary to avoid noise spreading, ideally done manually
    raw = mark_bad_channels(raw)
    # Apply Maxwell filtering with head motion correction
    raw = mne.preprocessing.maxwell_filter(raw, head_pos=head_pos, calibration=calibration, cross_talk=cross_talk)
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

def remove_eog_ecg(ica, raw):
    eog_indices, eog_scores = ica.find_bads_eog(raw)
    ecg_indices, ecg_scores = ica.find_bads_ecg(raw, method='correlation')  # Default method 'ctps' identified too many components as heartbeat artifacts
    ica.exclude = eog_indices + ecg_indices
    ica.apply(raw)
    return raw

def filter_data(raw, l_freq=0.1, h_freq=100, line_freqs=(50,100)):
    # l_freq and h_freq: bandpass filter
    # line_freqs: power line artifatcs (default values are because data was recorded in UK)
    meg_picks = mne.pick_types(raw.info, meg=True)  #Only filter MEG channels
    raw.notch_filter(freqs=line_freqs, picks=meg_picks)  #Use a notch filter to take out power line noise
    raw.filter(l_freq=l_freq, h_freq=h_freq, picks=meg_picks) #Bandpass filter data (probably not any detectable high gamma activity in resting state because SNR is too low)
    return raw

def fit_ICA(raw, reject, random_state, picks, method = "picard", n_components = 40):
    ica = mne.preprocessing.ICA(n_components=40, method=method, random_state=random_state)
    try:
        ica.fit(raw, picks=picks, reject=reject)
    except:
        print("ICA could not run. Large environmental artifacts.\n")
    return ica

def remove_EOG_artifact(raw, ica, reject):
    eog_epochs = mne.preprocessing.create_eog_epochs(raw, reject=reject)
    if eog_epochs.events.size != 0:
        eog_inds, scores = ica.find_bads_eog(eog_epochs)
        if len(eog_inds) != 0:
            ica.exclude.extend(eog_inds)
        else:
            print("No ICA component correlated with EOG\n")
    else:
        print("No EOG events found\n")
    return ica

def remove_ECG_artifact(raw, ica, method='ctps', tmin=-.5, tmax=.5):
    ecg_epochs = mne.preprocessing.create_ecg_epochs(raw, tmin=tmin, tmax=tmax)
    if ecg_epochs.events.size != 0:
        ecg_inds, scores = ica.find_bads_ecg(ecg_epochs, method=method)
        if len(ecg_inds) != 0:
            ica.exclude.extend(ecg_inds)
        else:
            print("No ICA component correlated with ECG\n")
    else:
        print("No ECG events found\n")
    return ica

def do_ICA(raw, picks, reject = dict(mag=5e-12, grad=4000e-13), random_state = 23):
    ica = fit_ICA(raw, picks=picks, method = "fastica", reject = reject, random_state = random_state)
    ica = remove_EOG_artifact(raw, ica, reject = reject)
    ica = remove_ECG_artifact(raw, ica)
    ica.apply(raw)
    return raw, ica

