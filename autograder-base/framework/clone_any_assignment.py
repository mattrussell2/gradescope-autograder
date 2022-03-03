#!/bin/env python3
#
#              Clone any assignment
#
#     Argument: name of an assignment directory like /comp/11/grading/hw02
#
#     This creates underneath the current directory a dir named (in this case) hw02
#     and fills it with the latest submissions from the source
#

import os, sys, shutil
from latest_submission import latest_submission_dirs

def create_dir_if_needed(d):
    if not os.path.isdir(d):
        os.mkdir(d)

#  Check command line arg
assert len(sys.argv) == 2, "Usage: %s <grading_dir>" % sys.argv[0]

sourcedir = sys.argv[1].rstrip('/')


base, hw = os.path.split(sourcedir)   # we assume hw dir is last component

assert base.endswith("/grading"), "%s must be a Tufts CS dept grading directory (must contain ../grading/.. in name)" % sourcedir

#
#  Make local directory if needed and change to it
#
create_dir_if_needed(hw)

#
# Copy the submissions
#
os.chdir(hw)
for d in latest_submission_dirs(sourcedir):
    print("Copying %s to %s" % (d, hw), file=sys.stderr)
    ignore, submission = os.path.split(d)
    shutil.copytree(d, submission)








