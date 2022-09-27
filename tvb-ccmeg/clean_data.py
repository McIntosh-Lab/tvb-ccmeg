#!/bin/env python
#
# Script name: clean_data.py
#
# Description: Script to apply max filtering to data
#
# Author: Kelly Shen
#
# License: BSD (3-clause)

import sys

import mne
import library as lib
import numpy as np

def detect_and_maxfilter(raw, coord_frame):
    
    print(coord_frame)
    
    # Detect bad channels automatically, rather than reading from file #PJ
    bads = lib.preprocessing.detect_bad_channels(raw, coord_frame)

    raw.info['bads'] = bads
    
    max_filtered = lib.preprocessing.run_maxfilter(raw, coord_frame=coord_frame)
    return max_filtered




if __name__ == "__main__":
    # args = sys.argv[1:] # three args: raw,subject,kind
    # assume order of raw, coord_frame)
    # also assume these are file paths
    raw = np.load(sys.argv[1])
    coord_frame = np.load(sys.argv[2])
    save_path = sys.argv[3]

    filtered = run_maxfilter(raw, coord_frame)
    np.save(save_path, filtered)
