#!/bin/env python
#
# Author: Denis A. Engemann <denis.engemann@gmail.com> & Kelly Shen
#
# License: BSD (3-clause)

import os
import os.path as op
import random

import numpy as np

from sklearn.covariance import oas
from scipy.stats import pearsonr

import mne
from mne.minimum_norm import make_inverse_operator, apply_inverse_epochs
import mne_bids

from joblib import Parallel, delayed
from autoreject import get_rejection_threshold

import config as cfg
import library as lib
import stage_data
import clean_data


#N_JOBS = 40

#max_filter_info_path = op.join(
#    cfg.camcan_meg_path,
#    "data_nomovecomp/"
#    "aamod_meg_maxfilt_00001")





def _apply_inverse_cov(
        cov, info, nave, inverse_operator, lambda2=1. / 9., method="dSPM",
        pick_ori=None, prepared=False, label=None,
        method_params=None, return_residual=False, verbose=None,
        log=True):
    """Apply inverse operator to evoked data HACKED
    """
    from mne.minimum_norm.inverse import _check_reference
    from mne.minimum_norm.inverse import _check_ori
    from mne.minimum_norm.inverse import _check_ch_names
    from mne.minimum_norm.inverse import _check_or_prepare
    from mne.minimum_norm.inverse import _check_ori
    from mne.minimum_norm.inverse import _pick_channels_inverse_operator
    from mne.minimum_norm.inverse import _assemble_kernel
    from mne.minimum_norm.inverse import _subject_from_inverse
    from mne.minimum_norm.inverse import _get_src_type
    from mne.minimum_norm.inverse import combine_xyz
    from mne.minimum_norm.inverse import _make_stc
    from mne.utils import _check_option
    from mne.utils import logger
    from mne.io.constants import FIFF
    from collections import namedtuple

    INVERSE_METHODS = ['MNE', 'dSPM', 'sLORETA', 'eLORETA']

    fake_evoked = namedtuple('fake', 'info')(info=info)

    _check_reference(fake_evoked, inverse_operator['info']['ch_names'])
    _check_option('method', method, INVERSE_METHODS)
    if method == 'eLORETA' and return_residual:
        raise ValueError('eLORETA does not currently support return_residual')
    
    # PJ - the next line causes an error (_check_ori missing positional arg 'src')
    #_check_ori(pick_ori, inverse_operator['source_ori'])

    
    #
    #   Set up the inverse according to the parameters
    #

    _check_ch_names(inverse_operator, info)

    inv = _check_or_prepare(inverse_operator, nave, lambda2, method,
                            method_params, prepared)

    #
    #   Pick the correct channels from the data
    #
    sel = _pick_channels_inverse_operator(cov['names'], inv)
    logger.info('Applying inverse operator to cov...')
    logger.info('    Picked %d channels from the data' % len(sel))
    logger.info('    Computing inverse...')

    K, noise_norm, vertno, source_nn = _assemble_kernel(inv, label, method,
                                                        pick_ori)
    
    # apply imaging kernel
    sol = np.einsum('ij,ij->i', K, (cov.data[sel] @ K.T).T)[:, None]

    is_free_ori = (inverse_operator['source_ori'] ==
                   FIFF.FIFFV_MNE_FREE_ORI and pick_ori != 'normal')

    if is_free_ori and pick_ori != 'vector':
        logger.info('    Combining the current components...')
        sol = combine_xyz(sol)

    if noise_norm is not None:
        logger.info('    %s...' % (method,))
        if is_free_ori and pick_ori == 'vector':
            noise_norm = noise_norm.repeat(3, axis=0)
        sol *= noise_norm

    tstep = 1.0 / info['sfreq']
    tmin = 0.0
    subject = _subject_from_inverse(inverse_operator)

    src_type = _get_src_type(inverse_operator['src'], vertno)
    if log:
        sol = np.log10(sol, out=sol)

    stc = _make_stc(sol, vertno, tmin=tmin, tstep=tstep, subject=subject,
                    vector=(pick_ori == 'vector'), source_nn=source_nn,
                    src_type=src_type)
    logger.info('[done]')

    return stc


def _compute_mne_power(subject, kind, freqs):

#    ###########################################################################
#    # Compute source space
#    # -------------------
#    src = mne.setup_source_space(subject, spacing='oct6', add_dist=False,
#                                 subjects_dir=cfg.mne_camcan_freesurfer_path)
#    
#    
#    '''
#    # This section was added to compute the transform from head coords to MRI coords (rather than using Krieger/Halifax" #PJ
#    # Update - now using the Halifax transforms provided by Tim Bardouille https://github.com/tbardouille/camcan_coreg #PJ
#    
#    meg_bids_path = mne_bids.BIDSPath(subject=subject[4:], root=cfg.camcan_meg_raw_path, session='rest', task='rest', extension='.fif', check=False)
#    t1_bids_path = mne_bids.BIDSPath(subject=subject[4:], root=cfg.camcan_path + '/mri/pipeline/release004/BIDS_20190411/anat')
#    trans = mne_bids.get_head_mri_trans(meg_bids_path,
#                                        t1_bids_path = t1_bids_path,
#                                        fs_subject=subject,
#                                        fs_subjects_dir=cfg.mne_camcan_freesurfer_path)
#    '''
#    
#    # Get transform filename #PJ
##    trans = trans_map[subject]
#    
#    # Load boundary element model - Assumes run_make_boundary_element_models.py already run #PJ
#    bem = cfg.mne_camcan_freesurfer_path + \
#        "/%s/bem/%s-meg-bem.fif" % (subject, subject)
#
#
#
#    # Compute covariance in empty room recording for MNE #PJ
#    cov = mne.compute_raw_covariance(filtered_rejected_er, method='oas')
#    
#    # compute before band-pass of interest
#
#    event_length = 5.
#    event_overlap = 0.
#    filtered_length = filtered_rejected.times[-1]
#    events = mne.make_fixed_length_events(
#        filtered_rejected,
#        duration=event_length, start=0, stop=filtered_length - event_length)
#
#    #######################################################################
#    # Compute the forward and inverse
#    # -------------------------------
#
#    info = mne.Epochs(filtered_rejected, events=events, tmin=0, tmax=event_length,
#                      baseline=None, reject=None, preload=False,
#                      decim=10).info
#    fwd = mne.make_forward_solution(info, trans, src, bem)
#    inv = make_inverse_operator(info, fwd, cov)
#    del fwd
#
#    #######################################################################
#    # Compute label time series and do envelope correlation ### I think he meant 'covariance' #PJ
#    # -----------------------------------------------------
#    
#    # This section gets surface source labels from MNE sample data #PJ
#    
#    #mne_subjects_dir = "/storage/inria/agramfor/MNE-sample-data/subjects"
#    
#    sample_data_folder = mne.datasets.sample.data_path()
#    mne_subjects_dir = os.path.join(sample_data_folder, 'subjects')
#    
#    #labels = mne.read_labels_from_annot('fsaverage', 'aparc_sub',
#    #                                    subjects_dir=mne_subjects_dir)
#    
#    # not sure difference between aparc_sub and aparc_a2009s #PJ
#    labels = mne.read_labels_from_annot('fsaverage', 'aparc.a2009s',
#                                        subjects_dir=mne_subjects_dir)
#    
#    # Warp labels to this subject's surface #PJ
#    labels = mne.morph_labels(
#        labels, subject_from='fsaverage', subject_to=subject,
#        subjects_dir=cfg.mne_camcan_freesurfer_path)
#    labels = [ll for ll in labels if 'unknown' not in ll.name]

    
    # Band-pass signal to frequency band, compute sensor covariance, project to surface labels, compute covariance between labels #PJ
    results = dict()
    
    for fmin, fmax, band in freqs:
        print(f"computing {subject}: {fmin} - {fmax} Hz")
        this_filtered = filtered_rejected.copy()
        this_filtered.filter(fmin, fmax, n_jobs=1) 
        reject = clean_data.get_global_reject_epochs(this_filtered, decim=5) # Get rejection threshold for band
        epochs = mne.Epochs(this_filtered, events=events, tmin=0, tmax=event_length,
                            baseline=None, reject=reject, preload=True,
                            decim=5)
        if DEBUG:
            epochs = epochs[:3]

        # MNE cov mapping
        data_cov = mne.compute_covariance(epochs, method='oas')

        # Next two calls compute average power at each label?? #PJ
        stc = _apply_inverse_cov(
            cov=data_cov, info=epochs.info, nave=1,
            inverse_operator=inv, lambda2=1. / 9.,
            pick_ori='normal', method='MNE', log=False)
        # assert np.all(stc.data < 0)

        label_power = mne.extract_label_time_course(
            stc, labels, inv['src'], mode="mean")  # XXX signal should be positive

        # Compute band-limited time course at each vertex #PJ
        stcs = apply_inverse_epochs(
            epochs, inv, lambda2=1. / 9.,
            pick_ori='normal',
            method='MNE',
            return_generator=True)

        # Get band-limited time course at each label from stcs #PJ
        label_ts = np.concatenate(mne.extract_label_time_course(
            stcs, labels, inv['src'], mode="pca_flip", # PCA flip prevents random sign flips from cancelling out #PJ
            return_generator=False), axis=-1)

        # Compute label x label covariance matrix using Oracle Approximating Shrinkage Estimator #PJ
        label_cov, _ = oas(label_ts.T, assume_centered=True)
        
        # Could try envelope correlation here (not debugged): #PJ
        #from mne_connectivity import envelope_correlation
        #corr = envelope_correlation(label_ts, verbose=True)
        #corr = envelope_correlation(np.reshape(label_ts, [1,150,-1]), verbose=True)
        
        #label_ts = mne.extract_label_time_course(stcs, labels, inv['src'], return_generator=True)
        #corr = envelope_correlation(label_ts, verbose=True)
        

        if DEBUG:
            print(
                pearsonr(
                    np.log10(np.diag(label_cov)).ravel(),
                    np.log10(label_power.ravel())))

        result = {'cov': label_cov[np.triu_indices(len(label_cov))], 
                  'power': label_power, 'subject': subject,
                  'fmin': fmin, 'fmax': fmax, "band": band,
                  'label_names': [ll.name for ll in labels]}
        results[band] = result
        
        if False:
            out_fname = op.join(
                cfg.derivative_path,
                f'{subject + ("-debug" if DEBUG else "")}_'
                f'cov_mne_{band}.h5')

            mne.externals.h5io.write_hdf5(
                out_fname, result, overwrite=True)
            
    return results       


#def _run_all(subject, freqs, kind='rest'):
def _run_all(subject, freqs, kind='ses-rest'):
    mne.utils.set_log_level('warning')
    # mne.utils.set_log_level('info')
    print(subject)
    error = 'None'
    result = dict()
    if not DEBUG:
        try:
            out = _compute_mne_power(subject, kind, freqs)

        except Exception as err:
            error = repr(err)
            print(error)
    else:
        out = _compute_mne_power(subject, kind, freqs)

    if error != 'None':
        out = {band: None for _, _, band in freqs}
        out['error'] = error

    return out

# Define frequency bands of interest #PJ
freqs = [(0.1, 1.5, "low"),
         (1.5, 4.0, "delta"),
         (4.0, 8.0, "theta"),
         (8.0, 15.0, "alpha"),
         (15.0, 26.0, "beta_low"),
         (26.0, 35.0, "beta_high"),
         (35.0, 50.0, "gamma_lo"),
         (50.0, 74.0, "gamma_mid"),
         (76.0, 120.0, "gamma_high")]



#DEBUG = True
#if DEBUG:
#    N_JOBS = 1
    
    # Just include test subjs for now # PJ
    #test_subjs = ['sub-CC320107', 'sub-CC420356', 'sub-CC510392', 'sub-CC221954']
#    test_subjs = ['sub-CC221954']
#    subjects = test_subjs
#    trans_map = {this_subj: trans_map[this_subj] for this_subj in test_subjs }
    
    # Just two freq bands for now #PJ
#    freqs = freqs[2:4]

#out = Parallel(n_jobs=N_JOBS)(
#    delayed(_run_all)(subject=subject, freqs=freqs, kind='ses-rest')
#    for subject in subjects)


#out = _run_all(subject=subject, freqs=freqs, kind='ses-rest')

#out = {sub: dd for sub, dd in zip(subjects, out) if 'error' not in dd}

#mne.externals.h5io.write_hdf5(
#    op.join(cfg.derivative_path, 'all_mne_source_power.h5'), out,
#    overwrite=True)

#mne.externals.h5io.write_hdf5(
#    op.join(cfg.derivative_path, 'sub-CC221954_mne_source_power.h5'), out,
#    overwrite=True)

