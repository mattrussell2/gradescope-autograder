#!/usr/bin/env python3
import os
from pathlib import Path
import argparse
import shutil
import subprocess

TMPDIR         = 'temp_testing_dir'
ORIG_DIR       = os.getcwd()
AUTOGRADER_DIR = ORIG_DIR

ap = argparse.ArgumentParser()
ap.add_argument('-s', '--submission', type=str, default='./submission', help="submission folder path; default=./submission")
ap.add_argument('-j', '--num-jobs',   type=int, default=1, help="concurrent jobs; default=1; -1=number of available cores")
ap.add_argument('-d', '--destroy-test-dir', action='store_true', help="will destroy temporary directories created to test the submission")
ap.add_argument('-l', '--lengthy-output', action='store_true', help="will print lengthy output")

ARGS = vars(ap.parse_args())

try:        
    print("creating temporary build directory")
    if os.path.exists(TMPDIR):
        subprocess.run(['chmod', 'u+rwx', '-R', TMPDIR]) # in case autograder failed from before. 
        shutil.rmtree(TMPDIR)
    
    shutil.copytree('.', TMPDIR, dirs_exist_ok=True)
    
    # submission dir might not be the same as './submission', however './submission' might exist
    # in that case, remove the copied folder.
    submission_dir = os.path.join(TMPDIR, 'submission')
    if os.path.exists(submission_dir):
        shutil.rmtree(submission_dir)
    
    # copy the 'actual' submission dir
    shutil.copytree(ARGS['submission'], submission_dir, dirs_exist_ok=True)

    os.chdir(TMPDIR)

    import autograde
    print("running tests")
    outvec = ['-j', str(ARGS['num_jobs']), '-n']
    if ARGS['lengthy_output']:
        outvec.append('-l')
    autograde.run_autograder(outvec)   
    print("done!")
finally:
    os.chdir('..')
    if ARGS['destroy_test_dir'] and os.path.exists(TMPDIR):
        print("deleting temporary testing directory")
        shutil.rmtree(TMPDIR)
