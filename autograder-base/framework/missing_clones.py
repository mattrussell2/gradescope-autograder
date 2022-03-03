#!/bin/env python3
#
#              Missing Clones
#
#     Must be called in a directory containing clones, such as the ones resulting
#     from clone_any_assignment.
#     
#     Argument: name of an assignment directory like /comp/11/grading/hw02
#
#     Lists the submission names <e.g. student.n> for which 
#     the local directory has either no submission or an older one
#



import os, sys, shutil, os.path
from latest_submission import latest_submission_dirs

if (len(sys.argv) != 2 or 
    (sys.argv[1].startswith('-h')) or 
    (sys.argv[1].startswith('--h'))):
    print(
"""Must be called in a directory containing clones, such as the ones resulting from clone_any_assignment.
 
Argument: name of an assignment directory like /comp/11/grading/hw02

Lists the submission names <e.g. student.n> for which the local directory has either no submission or an older one
""", file=sys.stderr)
    sys.exit(1)

sourcedir = sys.argv[1].rstrip('/')

base, hw = os.path.split(sourcedir)   # we assume hw dir is last component

assert base.endswith("/grading"), "%s must be a Tufts CS dept grading directory (must contain ../grading/.. in name)" % sourcedir


latest_submissions = set(map(lambda d: os.path.split(d)[-1], latest_submission_dirs(sourcedir)))

local_submissions = set(map(lambda d: os.path.split(d)[-1], latest_submission_dirs('.')))

assert len(local_submissions)>0, "No submission clones in local directory"


missing_or_superceded = latest_submissions - local_submissions

for d in sorted(missing_or_superceded):
    print(d)









