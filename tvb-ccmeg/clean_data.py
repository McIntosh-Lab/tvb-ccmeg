#!/bin/env python
#
# Script name: clean_data.py
#
# Description: Apply max filtering & reject EOG/ECG epochs
#
# Author: Denis A. Engemann <denis.engemann@gmail.com> & Kelly Shen
#
# License: BSD (3-clause)

import sys, os

import mne
from autoreject import get_rejection_threshold

import library as lib
import numpy as np

def _run_maxfilter(raw, coord_frame):
    # default coord_frame = 'head'
    
    # Detect bad channels automatically, rather than reading from file #PJ
    bads = lib.preprocessing.detect_bad_channels(raw, coord_frame)

    raw.info['bads'] = bads
    
    filtered = lib.preprocessing.run_maxfilter(raw, coord_frame=coord_frame)

    return filtered


def _compute_add_ssp_exg(raw):
    reject_eog, reject_ecg = _get_global_reject_ssp(raw)

    proj_eog = mne.preprocessing.compute_proj_eog(
        raw, average=True, reject=reject_eog, n_mag=1, n_grad=1, n_eeg=1, n_jobs=-1)

    proj_ecg = mne.preprocessing.compute_proj_ecg(
        raw, average=True, reject=reject_ecg, n_mag=1, n_grad=1, n_eeg=1, n_jobs=-1)

    cleaned = raw.add_proj(proj_eog[0])
    cleaned = cleaned.add_proj(proj_ecg[0])
    
    return cleaned


def _get_global_reject_ssp(raw):
    eog_epochs = mne.preprocessing.create_eog_epochs(raw)
    if len(eog_epochs) >= 5:
        reject_eog = get_rejection_threshold(eog_epochs, decim=8) #check decim aliasing warning for here
        del reject_eog['eog']
    else:
        reject_eog = None

    ecg_epochs = mne.preprocessing.create_ecg_epochs(raw)
    if len(ecg_epochs) >= 5:
        reject_ecg = get_rejection_threshold(ecg_epochs, decim=8) #check decim aliasing warning for here
    else:
        reject_eog = None

    if reject_eog is None:
        reject_eog = reject_ecg
    if reject_ecg is None:
        reject_ecg = reject_eog
    return reject_eog, reject_ecg


def get_global_reject_epochs(raw, decim):
    duration = 3.
    events = mne.make_fixed_length_events(
        raw, id=3000, start=0, duration=duration)

    epochs = mne.Epochs(
        raw, events, event_id=3000, tmin=0, tmax=duration, proj=False,
        baseline=None, reject=None)
    epochs.apply_proj()
    epochs.load_data()
    epochs.pick_types(meg=True)
    reject = get_rejection_threshold(epochs, decim=decim)
    return reject


def clean_data(raw, raw_er):

    # Run MaxFilter without movement compensation (don't know why they run it without movement compensation - revisit) #PJ
    filtered = _run_maxfilter(raw, 'head')
    # Project EOG and ECG components out of raw data #PJ
    cleaned = _compute_add_ssp_exg(filtered)
    
    # maxfilter emptyroom data
    filtered_er = _run_maxfilter(raw_er, 'meg')
    # Add projections from rest recording to empty room (not sure why exactly) #PJ
    cleaned_er = filtered_er.add_proj(filtered.info["projs"])   
    
    return cleaned, cleaned_er



if __name__ == "__main__":
    # args = sys.argv[1:] # three args: raw,subject,kind
    # assume order of raw, coord_frame)
    # also assume these are file paths
    raw = np.load(sys.argv[1])
    coord_frame = np.load(sys.argv[2])
    save_path = sys.argv[3]

    filtered = run_maxfilter(raw, coord_frame)
    np.save(save_path, filtered)
