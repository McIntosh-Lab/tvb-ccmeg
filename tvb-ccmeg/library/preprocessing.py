import os.path as op
import mne
from mne.preprocessing import find_bad_channels_maxwell

_curr_dir = op.dirname(op.realpath(__file__))


def run_maxfilter(raw, coord_frame='head', destination=None):
    """Run maxfilter."""
    cal = op.join(_curr_dir, 'sss_params', 'sss_cal.dat')
    ctc = op.join(_curr_dir, 'sss_params', 'ct_sparse.fif')

    raw = mne.preprocessing.maxwell_filter(
        raw, calibration=cal,
        cross_talk=ctc,
        st_duration=10.,
        st_correlation=.98,
        destination=destination,
        coord_frame=coord_frame)
    return raw


#def parse_bad_channels(sss_log):
#    """Parse bad channels from sss_log."""
#    with open(sss_log) as fid:
#        bad_lines = {l for l in fid.readlines() if 'Static bad' in l}
#    bad_channels = list()
#    for line in bad_lines:
#        chans = line.split(':')[1].strip(' \n').split(' ')
#        for cc in chans:
#            ch_name = 'MEG%01d' % int(cc)
#            if ch_name not in bad_channels:
#                bad_channels.append(ch_name)
#    return bad_channels

def detect_bad_channels(raw, coord_frame='head'):
    """Auto detect bad channels using Maxwell filtering"""
    cal = op.join(_curr_dir, 'sss_params', 'sss_cal.dat')
    ctc = op.join(_curr_dir, 'sss_params', 'ct_sparse.fif')
    
    auto_noisy_chs, auto_flat_chs = find_bad_channels_maxwell(
                                    raw, calibration=cal,
                                    cross_talk=ctc,
                                    coord_frame=coord_frame)
    
    bad_channels = auto_noisy_chs + auto_flat_chs
    
    return bad_channels