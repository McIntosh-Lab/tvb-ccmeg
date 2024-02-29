#!/bin/env python
#
# Script name: stage_data.py
#
# Description: load and get Cam-CAN MEG data ready for pipe
#
# Authors: Denis A. Engemann <denis.engemann@gmail.com> & Kelly Shen
#
# License: BSD (3-clause)

import os
import os.path as op
import random

import mne

import config as cfg


def _get_meg(subject, task):                      
    fname = op.join(cfg.camcan_meg_raw_path, subject, task, 'meg', '%s_%s_task-rest_meg.fif' % (subject, task))
    raw = mne.io.read_raw_fif(fname)
    mne.channels.fix_mag_coil_types(raw.info) #Fixes size labelling for some coils # PJ
    return raw


def _get_transform(subject):
    trans = 'trans-halifax'     # using the Halifax transforms provided by Tim Bardouille https://github.com/tbardouille/camcan_coreg #PJ
    found = os.listdir(op.join(cfg.derivative_path, trans))
    found_subj = [sub for sub in found if subject in sub][0]
    return op.join(cfg.derivative_path, trans, found_subj)


def _get_empty_room(subject):
    fname_er = op.join(cfg.camcan_meg_path, "emptyroom", subject, "emptyroom", "emptyroom_%s.fif" % subject[4:])
    raw_er = mne.io.read_raw_fif(fname_er)
    mne.channels.fix_mag_coil_types(raw_er.info)   
    return raw_er


def stage_data(subject, task):
    meg_raw = _get_meg(subject, task)
    trans_fname = _get_transform(subject)
    meg_emptyroom = _get_empty_room(subject)
    return meg_raw, trans_fname, meg_emptyroom


   
                      
# Why were they arbitrarily cropping??
#    if DEBUG:
#        # raw.crop(0, 180)
#        raw.crop(0, 120)
#    else:
#        raw.crop(0, 300)
        
        
