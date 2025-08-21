#!/bin/env python
#
# Module name: compute_source.py
#
# Description: Functions to compute source activity for Cam-CAM MEG data
#
# Authors: Simon Dobri <simon_dobri@sfu.ca> & Jack Solomon <jack_solomon@sfu.ca> & Santiago Flores <santiago_flores_alonso@sfu.ca>
#
# License: BSD (3-clause)

import mne
import os
import numpy as np
import scipy

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
    morph = mne.compute_source_morph(stc, subject_from=subject, subject_to='fsaverage6', subjects_dir=fs_dir)
    stc_fsavg = morph.apply(stc)
    return stc_fsavg, morph

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
        np.save(os.path.join(output_dir, 'parc_ts_beamformer_schaefer'), schaefer_ts)
        return labels_aparc, labels_schaefer, aparc_ts, schaefer_ts

def PSD_per_timeseries(data, bands, sfreq, h_freq, n_fft, window = 'hann', overlap = 2, norm_method = "z_score"):
    """
    Computes the Power Spectral Density (PSD) and band power for each vertex
    in a SourceEstimate (stc) object.

    Parameters:
        data (ndarray): numpy.ndarray
            An array of time series to decompose.
        sfreq (int): Sampling frequency of the data.
        bands (dict): Dictionary with band names and frequency ranges.
        h_freq (int): Integer defining the upper limit of the decomposition.
        n_fft (int): FFT size.
        window (string): window type for FFT. Default is 'hann'.
        overlap (int): Amount of overlap between FFT windows. 
            Default to 50% overlap (defined using the equation: n_fft//perc_overlap).
        See https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.get_window.html for different window types.
        norm_method (string): either "z_score" or "percentile".
            Used to define the normalization protocol of the pwoer spectrum

    Returns:
        psd_normalized: ndarray
            Normalized PSD for each vertex.
        band_powers: dict
            Average power for each frequency band per vertex.
    """

    n_overlap = n_fft // overlap

    # Compute PSD for all vertices
    psd, frequencies = mne.time_frequency.psd_array_welch(
        data, 
        fmin = 0, 
        fmax = h_freq, 
        sfreq = sfreq, 
        n_fft = n_fft,
        n_overlap=n_overlap,
        window = window)

    # Normalize PSD
    if norm_method == "z_score":
        psd_normalized = (psd - psd.mean(axis = 1, keepdims = True)) / np.std(psd, axis = 1, keepdims= True)
    elif norm_method =="percentile":
        psd_normalized = psd / psd.sum(axis=1, keepdims=True)
    else:
        raise ValueError("norm_method must be 'z_score' or 'percentile'.")

    # Compute power for each frequency band
    band_powers = {
        band: psd_normalized[:, (frequencies >= fmin) & (frequencies <= fmax)].mean(axis=1)
        for band, (fmin, fmax) in bands.items()
    }

    return psd_normalized, frequencies, band_powers
