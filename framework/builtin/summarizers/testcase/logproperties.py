#!/usr/sup/bin/python
#
#                          logproperties.py
#
#         Utility routines for extracting execution results from logs
#         and results files
#

#
#                      exectutionResults
#
#      Override these to (respectively) hook the location and parsing of
#      exitcode information and/or the representation of results in the summary
#

import asciijson

def exitCodeDictionary(testcase):
    exitcodefilename = testcase.exitcodefilename()
    try:
        with open(exitcodefilename, "r") as exitcodefile:
            exitcodeJSON = exitcodefile.read()
            exitcodeDict = asciijson.loads(exitcodeJSON)
    except IOError as e:
        exitcodeDict = {"failure" : "No Exitcode Recorded"}
    return exitcodeDict


def valgrindDictionary(testcase):
    valgrindJSONfilename = testcase.valgrindJSONfilename()
    try:
        with open(valgrindJSONfilename, "r") as valgrindfile:
            valgrindJSON = valgrindfile.read()
            valgrindDict = asciijson.loads(valgrindJSON)
    except IOError as e:
        valgrindDict = None
    return valgrindDict


