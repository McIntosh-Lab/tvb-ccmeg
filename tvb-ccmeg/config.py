
import os.path as op

#camcan_path = '/project/def-rmcintos/pjohns/ccmeg/ccmeg_data/'
camcan_path = '/home/kshen/scratch/ccmeg/ccmeg_data/'

#camcan_meg_path = op.join(
#        camcan_path, 'meg/pipeline/release005/BIDSsep/') #release 005
camcan_meg_path = op.join(camcan_path, 'camCAN724/cc700/meg/pipeline/release005/BIDSsep/')

#camcan_meg_raw_path = op.join(camcan_meg_path, 'rest') #release 005
camcan_meg_raw_path = op.join(camcan_meg_path, 'rest')

#derivative_path = '/liberatrix/mcintosh_lab/camcan-meg/camcan_derivatives'
derivative_path = op.join(camcan_path, 'camcan_derivatives')

#mne_camcan_freesurfer_path = (
#	 '/tolosa/mcintosh_lab/pjohnston/camcan_derivatives/freesurfer')
mne_camcan_freesurfer_path = op.join(derivative_path, 'freesurfer')