#!/bin/env python
#
# Module name: compute_source.py
#
# Description: Functions to compute source activity for Cam-CAM MEG data
#
# Author: Simon Dobri <simon_dobri@sfu.ca>
#
# License: BSD (3-clause)

import mne

def setup_source_space(subject, subjects_dir):
    # Requires BEM surfaces to be computed in FreeSurfer directory
    # Could compute BEM surfaces in this module (done in MNE Python, not FreeSurfer)
    src = mne.setup_source_space(subject, spacing='oct6', surface='orig', add_dist=False, subjects_dir=subjects_dir)
    return src

def make_bem(subject, subjects_dir):
    # Requires BEM surfaces to be computed in FreeSurfer directory
    # Could compute BEM surfaces in this module (done in MNE Python, not FreeSurfer)
    conductivity = (0.3,)   # Single layer for MEG
    model = mne.make_bem_model(subject=subject, ico=4, conductivity=conductivity, subjects_dir=subjects_dir)
    bem = mne.make_bem_solution(model)
    return bem

def make_inverse_operator(raw, raw_fname, trans, src, bem, noise_cov):
    # Make forward solution
    fwd = mne.make_forward_solution(raw_fname, trans=trans, src=src, bem=bem, meg=True, eeg=False, mindist=5.0, n_jobs=None)
    # Make inverse operator
    inverse_operator = mne.minimum_norm.make_inverse_operator(raw.info, fwd, noise_cov, loose=0.2, depth=0.8)
    return inverse_operator

def compute_inverse_solution_rest(raw, inverse_operator, tmin=30, tmax=330):
    method = "dSPM"
    snr = 1.0           # Lower SNR for resting state than evoked responses
    lambda2 = 1./snr**2
    start, stop = raw.time_as_index([tmin, tmax])   # Range of time where we compute source activity
    stc = mne.minimum_norm.apply_inverse_raw(raw, inverse_operator, lambda2, start=start, stop=stop, method=method, pick_ori=None)
    return stc
