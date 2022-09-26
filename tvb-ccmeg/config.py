
import os.path as op

#camcan_path = '/storage/store/data/camcan'
#camcan_path = '/liberatrix/mcintosh_lab/camCAN724/cc700'
#camcan_path = '/tolosa/mcintosh_lab/pjohnston/camcan_test/'
#camcan_path = '/project/def-rmcintos/pjohns/ccmeg/ccmeg_data/'
camcan_path = '/home/kshen/scratch/ccmeg/ccmeg_data/'


#camcan_meg_path = op.join(
#    camcan_path, 'camcan47/cc700/meg/pipeline/release004/')
#camcan_meg_path = op.join(
#        camcan_path, 'meg/pipeline/release004/BIDS_20190411/')
#camcan_meg_path = op.join(
#        camcan_path, 'meg/pipeline/release005/BIDSsep/') #release 005
camcan_meg_path = op.join(camcan_path, 'camCAN724/cc700/meg/pipeline/release005/BIDSsep/')

#camcan_meg_raw_path = op.join(camcan_meg_path, 'data/aamod_meg_get_fif_00001')
#camcan_meg_raw_path = op.join(camcan_meg_path, 'meg_rest_raw')
#camcan_meg_raw_path = op.join(camcan_meg_path, 'rest') #release 005
camcan_meg_raw_path = op.join(camcan_meg_path, 'rest')

# derivative_path = '/storage/store/derivatives/camcan/pipelines/base2018/MEG'
#derivative_path = '/storage/inria/agramfor/camcan_derivatives'
#derivative_path = '/liberatrix/mcintosh_lab/camcan-meg/camcan_derivatives'
derivative_path = op.join(camcan_path, 'camcan_derivatives')

#mne_camcan_freesurfer_path = (
#    '/storage/store/data/camcan-mne/freesurfer')
#mne_camcan_freesurfer_path = (
#    '/liberatrix/mcintosh_lab/camcan-meg/camcan_derivatives/freesurfer')
#mne_camcan_freesurfer_path = (
#	 '/tolosa/mcintosh_lab/pjohnston/camcan_derivatives/freesurfer')
mne_camcan_freesurfer_path = op.join(derivative_path, 'freesurfer')




