#!/bin/env python3
#
#                          has_tabs.py
#
#      Author: Noah Mendelsohn
#
#           Usage: has_tabs.py <filetocheck> <message_if_tabs_found>
#     
#      Simple program to check a file for tabs.
#
#      Exitcode 0 and silence if there are no tabs.
#      Exitcode 4 and stderr message (taken from arg2) 
#
#      Note: this interface is designed to be used with a testset.json that has
#      a successreport/criteria entry of:
#
#                "failureMessage" : [ "stderr" , { "not" : {"exitcode" : 4} }],
#
#      This will cause the failure reason in the test_results to be 
#      the <message_if_tabs_found>
#

import sys

TABCHAR = "\t"
NOTABS_EXIT_CODE  = 0
HASTABS_EXIT_CODE = 4

assert len(sys.argv)==3, "Usage: has_tabs.py <filetocheck> <message_if_tabs_found>"

with open(sys.argv[1], "r") as f:
    filecontents = f.read()

if TABCHAR in filecontents:
    print(sys.argv[2], file=sys.stderr)
    sys.exit(HASTABS_EXIT_CODE)
else:
    sys.exit(NOTABS_EXIT_CODE)
