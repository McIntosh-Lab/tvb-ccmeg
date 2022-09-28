#!/bin/env python
#
# Script name: pipeline.py
#
# Description: Main pipeline script to call pipeline functions in order
#
# Author: Kelly Shen
#
# License: BSD (3-clause)

import sys,argparse

import stage_data as stage
import clean_data as clean
import compute_cov_inverse_mne

# some stuff i may need later
#import os
#import os.path as op
#import mne

# some stuff i def need later
#import logging


class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main():
    parser = MyParser(description='Cam-CAN MEG pipe wrapper. Runs a single subject')
    parser.add_argument('-subj', dest="ID", type=str, nargs=1, help='subject ID')
    parser.add_argument('-ses', dest="session", type=str, nargs=1, help='task type, e.g., ses-rest')
    
    argsa = parser.parse_args()
    
    if (argsa.ID==None):
        parser.print_help()
        exit()
    
    if (argsa.session==None):
        parser.print_help()
        exit()
            
    subject = argsa.ID[0]
    task = argsa.session[0]
    
    print("Subject ID: ", subject)


    # specify some customizable pipeline parameters
    #N_JOBS = 1
    #freqs = freqs[2:4] # Just two freq bands for now #PJ
        
    meg_data, trans_fname, emptyroom_data = stage.stage_data(subject,task)

    cleaned_meg, cleaned_er = clean.clean_data(meg_data, emptyroom_data)
    
    print(cleaned_meg)
    print(cleaned_er)
    
#    out = Parallel(n_jobs=N_JOBS)(
    #delayed(_run_all)(subject=subject, freqs=freqs, kind='ses-rest')
    #for subject in subjects)

    
# points to big code block for now:
#compute_cov_inverse_mne    

#some pseudo code for later
# 1. module for i/o
# 2. clean_data.run_maxfilter(raw,'head')
# clean_data.run_maxfilter(raw_er,'meg')
   


# example command line usage:
# python pipeline.py -subj sub-CC221954 -ses ses-rest


if __name__ == "__main__":
    main()