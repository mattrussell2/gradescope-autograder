#!/bin/env python3
#
#              superceded.py
#
#     Arguments: names of two assignment directories from provide
#
#     Lists the submission names for any submissions newer in the first dir than
#     the second
#

import os, sys, shutil
from more_itertools import partition
from latest_submission import latest_submission_dirs

def login_from_dir(d):
    parts = os.path.basename(d).split('.')
    assert len(parts)==2, f"login_from_dir: directory not of form <login.n>: {d}"
    return parts[0]

def version_from_dir(d):
    parts = os.path.basename(d).split('.')
    assert len(parts)==2, f"version_from_dir: directory not of form <login.n>: {d}"
    return int(parts[1])

#  Check command line arg
assert len(sys.argv) == 3, "Usage: %s <provide_dir> <clone_dir>"  % sys.argv[0]

providedir = sys.argv[1].rstrip('/')
clonedir = sys.argv[2].rstrip('/')

# These are sets with entries of the form login.n
# 
latest_in_provide = set(os.path.basename(d) for d in latest_submission_dirs(providedir))
latest_in_clone = set(os.path.basename(d) for d in latest_submission_dirs(clonedir))

# These are set of login, not login.n
by_login_in_clone = {login_from_dir(d):d for d in latest_in_clone}
by_login_in_provide = {login_from_dir(d):d  for d in latest_in_provide}

brand_new = []
supercedes = []
# Split into new vs. updated
for login, provide_dir in by_login_in_provide.items():
    cloned_dir = by_login_in_clone.get(login, None)
    # If we got exactly the same one ignore
    if provide_dir == cloned_dir:
        continue   # we've got the exact same one
    # See if we've got one at all, if not, this is brand new
    if cloned_dir == None:
        brand_new.append(provide_dir)
    else:
        provide_version = version_from_dir(provide_dir)
        cloned_version = version_from_dir(cloned_dir)
        assert cloned_version <= provide_version, f"Cloned version {cloned_dir} already newer than latest provided version {provide_version}"
        # We now know that the provided vesion is newer
        supercedes.append(provide_dir)



print("New_dirs: " + ' '.join(brand_new))
print("Updated_dirs: " + ' '.join(supercedes))




