#!/bin/env python3
#
#                          has_longlines.py
#
#      Author: Noah Mendelsohn
#
#           Usage: has_longlines.py <filetocheck>  <maxOKlinesize> <message_if_longlines_found>
#     
#      Simple program to check a file for longlines.
#
#      Exitcode 0 and silence if there are no longlines.
#      Exitcode 4 and stderr message (taken from arg3) 
#      Exitcode 16 and message on stderr if contract violated
#
#      Note: this interface is designed to be used with a testset.json that has
#      a successreport/criteria entry of:
#
#                "failureMessage" : [ "stderr" , { "not" : {"exitcode" : 4} }]
#
#      This will cause the failure reason in the test_results to be 
#      the <message_if_longlines_found>
#

import sys

NO_LONGLINES_EXIT_CODE  = 0
HAS_LONGLINES_EXIT_CODE = 4

def usage():
    print("Usage: has_longlines.py <filetocheck> <maxOKlinesize> <message_if_longlines_found>\n ...maxOKlinesize must be an integer\nArglist = {}".format(repr(sys.argv[1:])), 
                                                                                                                                                         file=sys.stderr)
    sys.exit(16)

assert len(sys.argv) == 4, usage()

try:
    maxlen = int(sys.argv[2])
except ValueError as e:
    usage()

with open(sys.argv[1], "r") as f:
    longlines = [l for l in f.readlines() if len(l.rstrip("\n")) > maxlen]

# print("IN HAS LONGLINES: {} longlines={}".format(sys.argv[1:], longlines))
if len(longlines) > 0:
    print(sys.argv[3], file=sys.stderr)
    sys.exit(HAS_LONGLINES_EXIT_CODE)
else:
    sys.exit(NO_LONGLINES_EXIT_CODE)
