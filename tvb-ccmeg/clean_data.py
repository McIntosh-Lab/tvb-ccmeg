#!/bin/env python
#
# Script name: clean_data.py
#
# Description: Apply max filtering & reject EOG/ECG epochs
#
# Author: Kelly Shen
#
# License: BSD (3-clause)

import sys, os

import mne
from autoreject import get_rejection_threshold

import library as lib



def _get_global_reject_ssp(raw):
    eog_epochs = mne.preprocessing.create_eog_epochs(raw)
    if len(eog_epochs) >= 5:
        reject_eog = get_rejection_threshold(eog_epochs, decim=8)
        del reject_eog['eog']
    else:
        reject_eog = None

    ecg_epochs = mne.preprocessing.create_ecg_epochs(raw)
    if len(ecg_epochs) >= 5:
        reject_ecg = get_rejection_threshold(ecg_epochs, decim=8)
    else:
        reject_eog = None

    if reject_eog is None:
        reject_eog = reject_ecg
    if reject_ecg is None:
        reject_ecg = reject_eog
    return reject_eog, reject_ecg


def compute_add_ssp_exg(raw):
    reject_eog, reject_ecg = _get_global_reject_ssp(raw)

    proj_eog = mne.preprocessing.compute_proj_eog(
        raw, average=True, reject=reject_eog, n_mag=1, n_grad=1, n_eeg=1)

    proj_ecg = mne.preprocessing.compute_proj_ecg(
        raw, average=True, reject=reject_ecg, n_mag=1, n_grad=1, n_eeg=1)

    rejected = raw.add_proj(proj_eog[0])
    rejected = raw.add_proj(proj_ecg[0])
    return rejected


def run_maxfilter(raw, coord_frame):
    # default coord_frame = 'head'
    
    # Detect bad channels automatically, rather than reading from file #PJ
    bads = lib.preprocessing.detect_bad_channels(raw, coord_frame)
    print('bads coord_frame')
    print(coord_frame)

    raw.info['bads'] = bads
    
    filtered = lib.preprocessing.run_maxfilter(raw, coord_frame=coord_frame)
    print('filtered coord_frame')
    print(coord_frame)
    return filtered







if __name__ == "__main__":
    main()