#!/bin/env python3
#
#                       create_data_files.py
#                  Author: Noah Mendelsohn
#
#      Must be run in a testset directory. For all selected tests (defaults to
#      all tests), if both the "data" and "datafile" keys exist in the test
#      specification, then the corresponding data is written to the file.
#
#      Specifically str(data) is written, so ints are handled with default formatting.
#               

import set_of_tests
import argparse, os, sys

TESTSET_FILENAME = 'testset.json'
DEBUGOUT = False

DATA_KEY = "data"
DATAFILE_KEY = "datafile"

def debug_print(s):
    if DEBUGOUT:
        print(s,file=sys.stderr)

def error_print(s):
    print(s,file=sys.stderr)

#---------------------------------------------------------------
#                     counters
#---------------------------------------------------------------

number_of_files_written = 0
number_of_tests_skipped = 0

#---------------------------------------------------------------
#                     parseargs
#
#    Use Python standard argument parser to parse arguments and provide help
#---------------------------------------------------------------

def parseargs():
    parser = argparse.ArgumentParser("Write data files as specified in testset")
#    parser.add_argument("-format", nargs=1, help="Build a testset from a template", \
#                            choices=[JSONFORMATKEY, CSVFORMATKEY, COMP40FORMATKEY], \
#                            default=[COMP40FORMATKEY])
    parser.add_argument('testnames', help="Names of tests (default is all)", nargs="*")
    return parser.parse_args()

#---------------------------------------------------------------
#                    write_data_for_test
#
#       t.DATAFILE_key is name of file to write
#       t.DATA_KEY is data to write
#---------------------------------------------------------------

def write_data_for_test(t):
    global number_of_files_written, number_of_tests_skipped 
    if hasattr(t, DATA_KEY) and hasattr(t,DATAFILE_KEY):
        with open(getattr(t,DATAFILE_KEY), "w", newline="", encoding="ascii") as f:
            f.write(str(getattr(t, DATA_KEY)))
        number_of_files_written += 1
    else:
        error_print("Skipping test {}: {} and/or {} entries missing".
                    format(t.name, DATAFILE_KEY, DATA_KEY))
        number_of_tests_skipped += 1
    

#---------------------------------------------------------------
#                           main
#
#    Use Python standard argument parser to parse arguments and provide help
#---------------------------------------------------------------

args = parseargs()

#
#  Load the local testset.json

debug_print("Loading: " + TESTSET_FILENAME)

try:
    testset = set_of_tests.createTestsfromJSON(TESTSET_FILENAME)
except Exception as e:
    print("Error loading test configuration: {}".format(str(e)))
    raise

debug_print("Successfully loaded: " + TESTSET_FILENAME)

# 
# Go through all the input files and update the results
#

testnames = args.testnames

if not testnames:
    testnames = [test.name for test in testset]

debug_print("Testnames: " + repr(testnames))


tests = [test for test in testset if test.name in testnames]

debug_print("Names of gathered tests: " + repr([test.name for test in tests]))

#
#      Write the files
#
for t in tests:
    write_data_for_test(t)

error_print("{:d} files written; {:d} files skipped".format(number_of_files_written, number_of_tests_skipped))
