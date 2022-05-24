#!/usr/bin/python3
import os
from pathlib import Path
import argparse
import shutil
import subprocess

TMPDIR         = 'temp_ref_build_dir'
ORIG_DIR       = os.getcwd()
AUTOGRADER_DIR = ORIG_DIR

ap = argparse.ArgumentParser()      
ap.add_argument('-p', '--homework-path',  type=str, required=False, help="path to homework autograding directory")
ap.add_argument('-j', '--num-jobs',       type=int, default=1,      help="concurrent jobs; default=1; -1=number of available cores")
ap.add_argument('-a', '--autograder-dir', type=str, required=False, help="path to folder that contains autograde.py")
ap.add_argument('-k', '--keep-build-dir', action='store_true',      help="will not destroy temporary directory to build / run reference code")
ap.add_argument('-n', '--no-copy',        action='store_true',      help="will not copy reference files to [hw_path]/testset/ref_output")

ARGS = vars(ap.parse_args())

if not ARGS['homework_path']:
    print("ERROR: provide the path of the homework autograding directory")
    exit(1)
else:
    if ARGS['homework_path'][-1] == '/':
        ARGS['homework_path'] = ARGS['homework_path'][:-1]

if not os.path.exists(os.path.join(ARGS['homework_path'], 'testset')):
    print(f"ERROR: solution must be in {ARGS['homework_path']}/testset")
    exit(1)

if not os.path.exists(os.path.join(ARGS['homework_path'], 'testset', 'solution')):
    print(f"ERROR: solution folder must be in {ARGS['homework_path']}/testset")
    exit(1)

if ARGS['autograder_dir']:
    AUTOGRADER_DIR = ARGS['autograder_dir']
    if 'autograde.py' in AUTOGRADER_DIR: 
        AUTOGRADER_DIR = AUTOGRADER_DIR.split('autograde.py')[0]

if not os.path.exists(os.path.join(AUTOGRADER_DIR, 'autograde.py')):
    print(f"ERROR: autograde.py must be located in the directory this script is called from. " + \
           "If not, rerun with `autograde.py -a path/to/folder/that/contains/` autograde.py")

os.chdir(ARGS['homework_path'])

try:    
    print("creating temporary build directory")
    if os.path.exists(TMPDIR):
        subprocess.run(['chmod', 'u+rwx', '-R', TMPDIR]) # in case autograder failed from before. 
        shutil.rmtree(TMPDIR)

    shutil.copytree('.', TMPDIR, dirs_exist_ok=True)

    print("copying solution as submission")
    shutil.copytree(os.path.join("testset", "solution"), os.path.join(TMPDIR, "submission"))

    os.chdir(TMPDIR)
    shutil.copyfile(os.path.join(AUTOGRADER_DIR, 'autograde.py'), 'autograde.py')

    if not os.path.exists(os.path.join('testset','ref_output')):
        os.mkdir(os.path.join('testset','ref_output'))
    
    print("running tests")
    subprocess.run(["python3", "autograde.py", '-j', str(ARGS['num_jobs'])])

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
