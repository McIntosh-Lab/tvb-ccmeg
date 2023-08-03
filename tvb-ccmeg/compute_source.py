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

def compute_inverse_solution_rest(raw, inverse_operator, tmin=30, tmax=60, epoch_length=10):
    method = "dSPM"
    snr = 1.0           # Lower SNR for resting state than evoked responses
    lambda2 = 1./snr**2
    # Need to decide how much time we need: probably not the whole scan, and should be the same length of time for all participants
    cropped_raw = raw.copy().crop(tmin=tmin, tmax=tmax)
    # Divide into epochs to greatly speed up computation
    epochs = mne.make_fixed_length_epochs(cropped_raw, duration=epoch_length)
    stc = mne.minimum_norm.apply_inverse_epochs(epochs, inverse_operator, lambda2, method=method, pick_ori=None)
    return stc
