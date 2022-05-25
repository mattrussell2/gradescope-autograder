#!/usr/bin/python3
import os
from pathlib import Path
import argparse
import shutil
import subprocess
import autograde

TMPDIR         = 'temp_ref_build_dir'
ORIG_DIR       = os.getcwd()
AUTOGRADER_DIR = ORIG_DIR

ap = argparse.ArgumentParser()      
ap.add_argument('-j', '--num-jobs',       type=int, default=1, help="concurrent jobs; default=1; -1=number of available cores")
ap.add_argument('-k', '--keep-build-dir', action='store_true', help="will not destroy temporary directory to build / run reference code")
ap.add_argument('-n', '--no-copy',        action='store_true', help="will not copy reference files to [hw_path]/testset/ref_output")

ARGS = vars(ap.parse_args())

if not os.path.exists('testset'):
    print(f"ERROR: testset folder must exist")
    exit(1)

if not os.path.exists('testset', 'solution'):
    print(f"ERROR: solution folder must be in testset/")
    exit(1)

try:        
    print("creating temporary build directory")
    if os.path.exists(TMPDIR):
        subprocess.run(['chmod', 'u+rwx', '-R', TMPDIR]) # in case autograder failed from before. 
        shutil.rmtree(TMPDIR)

    shutil.copytree('.', TMPDIR, dirs_exist_ok=True)

    print("copying solution as submission")
    shutil.copytree(os.path.join("testset", "solution"), os.path.join(TMPDIR, "submission"))    
    os.chdir(TMPDIR)    
    
    if not os.path.exists(os.path.join('testset','ref_output')):
        os.mkdir(os.path.join('testset','ref_output'))
    
    print("running tests")
    autograde.run_autograder(['-j', str(ARGS['num_jobs'])])
   
    if not ARGS['no_copy']:
        print("copying output files to testset/ref_output")
        shutil.copytree(os.path.join("results", "output"), os.path.join("../testset/ref_output"), \
                        ignore=shutil.ignore_patterns("*.diff"), dirs_exist_ok=True)
    print("done!")
finally:
    os.chdir('..')
    if not ARGS['keep_build_dir'] and os.path.exists(ARGS['keep_build_dir']):
        print("deleting temporary build directory")
        shutil.rmtree(TMPDIR)
