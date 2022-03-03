#!/bin/env python3
#
#                             find_bad_json
#

import json
import os, sys
import traceback

#LOGFILE = "json_test.log"
LOGFILE = os.devnull

def check_json(fname, logfile):
    try:
        with open(fname) as f:
            json.load(f)
        
    except Exception as e:
        print(fname)
        print(f"Exception parsing file {fname}\n{traceback.format_exc()}")


filenames = sys.argv[1:]
for fname in filenames:
    check_json(fname, LOGFILE)
        
