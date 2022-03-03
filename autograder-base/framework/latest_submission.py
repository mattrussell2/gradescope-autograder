#!/bin/env python3

import glob, os

#
#             latest_submission_dirs
#
#     Returns an iterator over the latest submission dirs
#
def latest_submission_dirs(hw_dir):
    latest = {}    # key is login, value is submission as int
    for d in glob.iglob(os.path.join(hw_dir, "*.[1-9]")):
        # A little clumsy.  All bases are the same and we rely on that.
        base, submission = os.path.split(d)
        #
        #  submission is known to be in form xxx.n
        #
        login, number_string = submission.split('.')
        number = int(number_string)

        prev_latest = latest.get(login, -1)  # -1 is known to be below any real one
        latest[login] = max(prev_latest, number)
        
    # Since all bases are the same, we just use the last one
    return (os.path.join(base, '.'.join( (login, str(latest[login]) ))) for login in sorted(latest))


#
#   Test code
#
import sys
if __name__ == "__main__":
    print([d for d in latest_submission_dirs(sys.argv[1])])


        
    
