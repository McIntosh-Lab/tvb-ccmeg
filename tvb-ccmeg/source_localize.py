#!/bin/env python
#
# Script name: source_localize.py
#
# Description: epoch & source localize Cam-CAN MEG data
#
# Authors: Denis A. Engemann <denis.engemann@gmail.com> & Kelly Shen
#
# License: BSD (3-clause)

import mne

import config as cfg

# Get transform filename #PJ
#    trans = trans_map[subject]


def source_localize(subject, cleaned_er, cleaned_meg, trans):

    src = mne.setup_source_space(subject, spacing='oct6', add_dist=False,
                                 subjects_dir=cfg.mne_camcan_freesurfer_path)

    # Load boundary element model - Assumes run_make_boundary_element_models.py already run #PJ
    bem = cfg.mne_camcan_freesurfer_path + "/%s/bem/%s-meg-bem.fif" % (subject, subject)

    # Compute covariance in empty room recording for MNE #PJ
    cov = mne.compute_raw_covariance(cleaned_er, method='oas')
    
    # compute before band-pass of interest
    event_length = 5.
    event_overlap = 0.
    filtered_length = filtered_rejected.times[-1]
    events = mne.make_fixed_length_events(filtered_rejected,
        duration=event_length, start=0, stop=filtered_length - event_length)

    # Compute the forward and inverse
    info = mne.Epochs(cleaned_meg, events=events, tmin=0, tmax=event_length,
                      baseline=None, reject=None, preload=False,
                      decim=10).info
    fwd = mne.make_forward_solution(info, trans, src, bem)
    inv = make_inverse_operator(info, fwd, cov)
    del fwd

    
# This section gets surface source labels from MNE sample data #PJ #KS: Why??
def get_source_labels():
   
    sample_data_folder = mne.datasets.sample.data_path()
    mne_subjects_dir = os.path.join(sample_data_folder, 'subjects')
    
    #labels = mne.read_labels_from_annot('fsaverage', 'aparc_sub',
    #                                    subjects_dir=mne_subjects_dir)
    
    # not sure difference between aparc_sub and aparc_a2009s #PJ
    labels = mne.read_labels_from_annot('fsaverage', 'aparc.a2009s',
                                        subjects_dir=mne_subjects_dir)
    
    # Warp labels to this subject's surface #PJ
    labels = mne.morph_labels(
        labels, subject_from='fsaverage', subject_to=subject,
        subjects_dir=cfg.mne_camcan_freesurfer_path)
    labels = [ll for ll in labels if 'unknown' not in ll.name]