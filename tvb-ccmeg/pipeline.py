#!/bin/env python
#
# Script name: pipeline.py
#
# Description: Main pipeline script to call pipeline functions in order
#
# Author: Kelly Shen
#
# License: BSD (3-clause)

import sys,os,argparse
import logging
import errno

import stage_data as stage
import clean_data as clean
import compute_cov_inverse_mne

import config as cfg
import numpy as np


class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg
        
        
        
def main(args):

    
    if (args.ID==None):
        parser.print_help()
        exit()
    
    if (args.session==None):
        parser.print_help()
        exit()
            
    subject = args.ID[0]
    task = args.session[0]
    
    print("Subject ID: ", subject)


    if not args.outdir:
        outpath = f"{cfg.derivative_path}/{subject}"
    else:
        outpath = f"{args.outdir}/{subject}"
        
    try:
        os.mkdir(outpath)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        pass
        #add to log that directory exists as warning, remove 'pass'

    file_handler = logging.FileHandler(filename=f"{outpath}/{subject}-pipeline.log")
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    handlers = [file_handler, stdout_handler]

    logging.basicConfig(
            level=logging.DEBUG, 
            format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
            handlers=handlers
    )

    logger = logging.getLogger()

#    # Create and configure logger
#    logging.basicConfig(filename=f"{outpath}/{subject}-pipeline.log",
#                    format='%(asctime)s %(message)s',
#                    filemode='w')

#    log = logging.getLogger()
#    sys.stdout = LoggerWriter(log.debug)
#    sys.stderr = LoggerWriter(log.warning)

    #logger = logging.getLogger()
    # logger.setLevel(logging.DEBUG)

#    handler = logging.StreamHandler(sys.stdout)
    # handler.setLevel(logging.DEBUG)
#    formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
#    handler.setFormatter(formatter)
    # logger.addHandler(handler)
    


    # specify some customizable pipeline parameters
    #N_JOBS = 1
    #freqs = freqs[2:4] # Just two freq bands for now #PJ
        
    meg_data, trans_fname, emptyroom_data = stage.stage_data(subject,task)

    cleaned_meg, cleaned_er = clean.clean_data(meg_data, emptyroom_data)
    
    print(cleaned_meg)
    print(cleaned_er)
    

    
    cleaned_meg_npy = cleaned_meg.get_data()
    np.save(file=f"{outpath}/{subject}-cleaned-meg.npy", arr=cleaned_meg_npy)
    
    cleaned_er_npy = cleaned_er.get_data()
    np.save(file=f"{outpath}/{subject}-cleaned-er.npy", arr=cleaned_er_npy)
    
#    out = Parallel(n_jobs=N_JOBS)(
    #delayed(_run_all)(subject=subject, freqs=freqs, kind='ses-rest')
    #for subject in subjects)

    
# original big code block I'm grabbing these from:
#compute_cov_inverse_mne    

   


# example command line usage:
# python pipeline.py -subj sub-CC221954 -ses ses-rest



if __name__ == "__main__":
    
    
    
    parser = MyParser(description='Cam-CAN MEG pipe wrapper. Runs a single subject')
    parser.add_argument('-subj', dest="ID", type=str, nargs=1, help='subject ID')
    parser.add_argument('-ses', dest="session", type=str, nargs=1, help='task type, e.g., ses-rest')
    # parser.add_argument('-out', dest="outdir", type=str, nargs=1, default=os.getcwd(), help='output directory, default current wd')
    parser.add_argument('-out', dest="outdir", type=str, nargs=1, help='output directory, default current wd')
    
    args = parser.parse_args()
    
    print(args)
    main(args)
