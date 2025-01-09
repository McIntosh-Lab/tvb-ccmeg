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
import os
import numpy as np

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

def morph_2_fsaverage(stc, fs_dir, subject):
    morph = mne.compute_source_morph(stc, subject_from=subject, subject_to='fsaverage', subjects_dir=fs_dir)
    stc_fsavg = morph.apply(stc)
    return stc_fsavg

def parcellate_source_data(src, stc, subject, fs_dir, output_dir, Vol, mode='mean_flip'):
    if Vol:
        # Extract timeseries for aparc parcellated brain regions
        labels_aparc_aseg = fs_dir+subject+'/mri/aparc+aseg.mgz'
        with open(os.path.join(output_dir, 'aparc+aseg_labels.txt'),'w') as outfile:
            outfile.write('\n'.join(str(lab.name) for lab in labels_aparc_aseg))
        parc_ts_aparc_aseg = mne.extract_label_time_course(stc, labels_aparc_aseg, src, mode=mode)
        np.save(output_dir + 'parc_ts_beamformer_aparc', parc_ts_aparc_aseg)
        return labels_aparc_aseg, parc_ts_aparc_aseg
    else:
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
        aparc_ts = mne.extract_label_time_course(stc, labels_aparc, src, mode=mode)
        np.save(os.path.join(output_dir, 'parc_ts_beamformer_aparc'), aparc_ts)
        # Schaefer
        schaefer_ts = mne.extract_label_time_course(stc, labels_schaefer, src, mode=mode)
        np.save(os.path.join(output_dir, 'parc_ts_beamformer_Schaefer'), schaefer_ts)
        return labels_aparc, labels_schaefer, aparc_ts, schaefer_ts
