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

def run_maxfilter(raw, subject, kind, coord_frame):
    args = sys.argv[1:] # three args: raw,subject,kind
    
    print(coord_frame)
    
    # Detect bad channels automatically, rather than reading from file #PJ
    bads = lib.preprocessing.detect_bad_channels(raw, coord_frame)

    raw.info['bads'] = bads
    
    raw = lib.preprocessing.run_maxfilter(raw, coord_frame=coord_frame)
    return raw












if __name__ == "__main__":
    main()