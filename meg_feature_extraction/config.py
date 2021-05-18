
import os.path as op

#camcan_path = '/storage/store/data/camcan'
camcan_path = '/liberatrix/mcintosh_lab/'

#camcan_meg_path = op.join(
#    camcan_path, 'camcan47/cc700/meg/pipeline/release004/')
camcan_meg_path = op.join(
        camcan_path, 'camCAN724/cc700/meg/pipeline/release004/')

#camcan_meg_raw_path = op.join(camcan_meg_path, 'data/aamod_meg_get_fif_00001')
camcan_meg_raw_path = op.join(camcan_meg_path, 'BIDS_20190411/meg_rest_raw')


#mne_camcan_freesurfer_path = (
#    '/storage/store/data/camcan-mne/freesurfer')
mne_camcan_freesurfer_path = (
    '/opt/freesurfer6')

# derivative_path = '/storage/store/derivatives/camcan/pipelines/base2018/MEG'
#derivative_path = '/storage/inria/agramfor/camcan_derivatives'
derivative_path = '/liberatrix/mcintosh_lab/camcan-meg/camcan_derivatives'

