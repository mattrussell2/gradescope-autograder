#!/usr/sup/bin/python
# NEEDSWORK: above should be /bin/env python3 (Noah 12/29/2020)
#
#                  report_results.py
#
#        Author: Noah Mendelsohn
#      
#    Given one or more json files encoding the summaries of results of individual
#    testset runs, combine them into a table with one entry per test. Output the
#    results as json (default or -format json) or csv (-format csv switch) 
#    or on comp40 utln format (-format comp40)
#
#    NOTE: the main routine is at the bottom of this source file
#
#    MAJOR UPDATE (January 2021): All data gathering and cross referencing
#          has been moved to the new Results class, which also supplies 
#          simple formatters for JSON and CSV output. The goal is
#          to make it easy to create lots of results reporting programs like this,
#          even tailored to specific assignments. For compatibility with
#          existing deployments, this version continues to support all the features
#          of the old, factored one. In fact, the main logic here is to write
#          the COMP40-style reports and to handle the autograding hooks that Megan
#          Monroe and Richard Thompson implemented. Those should still work
#          as before.
#
#    NEEDSWORK: executable not found handled in crosstabs but not main
#               tables, thus shows only in comp 40 format
#        
#     

import argparse, os, sys, json, csv, os.path
import hook
from collections import OrderedDict

from results import Results        # Class that holds all the test results summary data

NOVALGRIND = "VALGRINDNOTRUN"      # marker value in output for when valgrind not run

#
#   Format names for use with command line -format argument
#
JSONFORMATKEY = 'json'
CSVFORMATKEY = 'csv'
COMP40FORMATKEY = 'comp40'

#---------------------------------------------------------------
#                     parseargs
#
#    Use Python standard argument parser to parse arguments and provide help
#---------------------------------------------------------------

def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-format", nargs=1, help="output format", \
                            choices=[JSONFORMATKEY, CSVFORMATKEY, COMP40FORMATKEY], \
                            default=[COMP40FORMATKEY])
    parser.add_argument("-progname", nargs=1, 
                        help="Name of tested program: used as title in some output reports")
    parser.add_argument('summaryFilenames', help="input testset summary files", nargs="+")
    args = parser.parse_args()
    return parser.parse_args()



#---------------------------------------------------------------
#                   writeCOMP40Report
#---------------------------------------------------------------


def writeCOMP40Report(resultsData, crossTotals, failureReasons, valgrindResults, progname):


    #
    #   Check to see if there is an autograder available
    #
    testsetdir = "%s/%s" % (os.environ.get('TS'), resultsData[0]["testset"])
    autoscoredir = "%s/autoscore" % (testsetdir)

    if os.path.isdir(autoscoredir):
        autograder = hook.load(testsetdir, 
                             "autoscore.autoscore", 
                             "get_grade")
    else:
        autograder = None
        # print("-- No autoscore module detected --", file=sys.stderr)
    


    #
    #   Write required COMP 40 preamble
    #
    # print("utln {}\n".format(resultsData[0]["testset"]))
    
    for student in sorted(crossTotals.keys()):
        #
        # Initialize and write preamble for student
        #
        groupTotals = crossTotals[student]
        valgrindTotals = valgrindResults[student]

        if autograder == None:
            pass
            # print("{}   I".format(student))
        else: 
            print("{}   {}".format(student, autograder(crossTotals[student], failureReasons[student], valgrindResults[student]))) 

        #
        # Initialize counts of tests  that succeeded, failed, etc.
        #
        failedTotal = 0
        timedoutTotal = 0
        successTotal = 0
        almostTotal = 0

        
        #
        # If -progname specified, write intro line
        #
        if progname:
            print("    Results of testing your {} progam:\n".format(progname))
            

        #
        #   Write one line report on each test set
        #
        for testset in groupTotals:
            testsetData = groupTotals[testset]
            numTests = len(testsetData["success"]) + len(testsetData["timedout"]) + \
                len(testsetData["failed"]) 
            almostCount = len(testsetData["almostsucceeded"])
            almostStr = " (almost passed {})".format(almostCount) if almostCount > 0 else ""
            print("    Passed {}, Failed {}{}, Timed out {} in testset {}".format( \
                  len(testsetData["success"]), \
                  len(testsetData["failed"]), \
                  almostStr, \
                  len(testsetData["timedout"]), \
                  testset))
            failedTotal += len(testsetData["failed"])
            timedoutTotal += len(testsetData["timedout"])
            successTotal += len(testsetData["success"])
            almostTotal += len(testsetData["almostsucceeded"])

        #
        #   If there were successes, report details
        #
        if successTotal > 0:
            def passedTests():
                for testset in groupTotals:
                    testsetData = groupTotals[testset]
                    for passedT in testsetData["success"]:
                        yield passedT[1]     # [0] is test name [1] is description
            formatWrapped(sys.stdout, sorted(passedTests()), 22, 75, \
                      firstPrefix="\n        Passed tests: ")


        #
        #   If there were successes, report details
        #
        if almostTotal > 0:
            def almostPassedTests():
                for testset in groupTotals:
                    testsetData = groupTotals[testset]
                    for passedT in testsetData["almostsucceeded"]:
                        yield passedT[1]     # [0] is test name [1] is description
            formatWrapped(sys.stdout, sorted(almostPassedTests()), 22, 75, \
                      firstPrefix="\n Almost Passed tests: ")


        #
        #   If there were failures, report details
        #
        if failedTotal > 0:
            def failedTests():
                for testset in groupTotals:
                    testsetData = groupTotals[testset]
                    for failedT in testsetData["failed"]:
                        if not failedT in testsetData["almostsucceeded"]:
                            yield failedT[1]     # [0] is test name [1] is description
            formatWrapped(sys.stdout, sorted(failedTests()), 22, 75, \
                      firstPrefix="\n        Failed tests: ")


            def failReasons():
                for msg, count in failureReasons[student].items():
                    yield "%s (%d)" % (msg, count)
            formatWrapped(sys.stdout, sorted(failReasons()), 22, 79, \
                      firstPrefix="\n     Failure reasons: ", sep=" ")

        #
        #   If there were timeouts, report details
        #
        if timedoutTotal > 0:
            def timedOutTests():
                for testset in groupTotals:
                    testsetData = groupTotals[testset]
                    for timedoutT in testsetData["timedout"]:
                        yield timedoutT[1] # [0] is test name [1] is description
                        
            formatWrapped(sys.stdout, sorted(timedOutTests()), 22, 75, \
                      firstPrefix="\n     Timed out tests: ")

        #
        #   If there were noteworthy valgrind results, report them
        #
        if valgrindTotals:
            print(valgrindTotals)
            def valgrindEvents():
                # iterate in desired output order
                eventTypes = ["Passed", "Errors", "DefinitelyLost", \
                                  "HeapInUse", "StillReachable"]
                totalValgrindTests = sum(valgrindTotals.values())
                for eventType in eventTypes:
                    if eventType in valgrindTotals:
                        yield "%s: %d / %d" %(eventType, valgrindTotals[eventType], totalValgrindTests)
            formatWrapped(sys.stdout, sorted(valgrindEvents()), 22, 75, \
                      firstPrefix="\n    Valgrind results: ")
        # if valgrindTotals:
        #     def valgrindEvents():
        #         # iterate in desired output order
        #         for eventType in ["Passed", "Errors", "DefinitelyLost", \
        #                           "HeapInUse", "StillReachable"]:
        #             if eventType in valgrindTotals:
        #                 # For C++
        #                 if eventType == "StillReachable":
        #                     yield "Passed with StillReachable: %d" %(valgrindTotals[eventType])
        #                 else:
        #                     yield "%s: %d" %(eventType, valgrindTotals[eventType])
        #     formatWrapped(sys.stdout, sorted(valgrindEvents()), 22, 75, \
        #               firstPrefix="\n    Valgrind results: ")
    
            
        print("\n")

    #
    #   Write required COMP 40 suffix
    #
    # print("<utln-names")
            
 

#---------------------------------------------------------------
#                   formatWrapped
#
#    Given an array (or other iterable) of strings, a 0-based
#    starting column, a column length in characters, prints
#    items from the list, separated by ", ", wrapping to make
#    the columns no longer than the specified length (so long as 
#    no one item needs overflow, in which case it is written anyway).
#
#    If firstPrefix is provided it should be a string of length startCol
#    containing the line to be used as the prefix the first time.
#
#---------------------------------------------------------------

def formatWrapped(fd, data, startCol, lineLength, firstPrefix=None, sep=None):
    # We use either the provided firstPrefix for first line or the usual blanks
    prefix = " " * startCol 
    firstTime = True
    outputLine = firstPrefix if firstPrefix else prefix
    separator = sep if sep else ", "
    for item in data:
        if not firstTime:
            outputLine+=separator
        firstTime = False
        if (len(outputLine) + len(item)) > lineLength:
            fd.write(outputLine)
            fd.write("\n")
            outputLine = prefix
        outputLine += item

    # 
    #   If unwritten data, then write it out
    #
    if (not firstTime) and len(outputLine) > startCol:
        fd.write(outputLine)
        fd.write("\n")
        

#---------------------------------------------------------------
#                          Main
#---------------------------------------------------------------

# - - - - - - - - - - - - - - - - - - - - - - - - 
#    Parse args and make sure all files are readable before starting
# - - - - - - - - - - - - - - - - - - - - - - - - 

args = parseargs()
format = args.format[0]
progname = args.progname[0] if args.progname else None

for summaryfilename in args.summaryFilenames:
    assert os.path.isfile(summaryfilename) and os.access(summaryfilename, os.R_OK), \
        "File %s does not exists or is not readable" % summaryfilename


# - - - - - - - - - - - - - - - - - - - - - - - - 
#   Gather data from input files
# - - - - - - - - - - - - - - - - - - - - - - - - 
# Not sure why this isn't working... need to ask Noah. For now trying to
# revert to previous version.

resultsData = Results(files=args.summaryFilenames)


# - - - - - - - - - - - - - - - - - - - - - - - - 
#       Generate output in the format requested
#       by the caller
# - - - - - - - - - - - - - - - - - - - - - - - - 

#
#   Output JSON format
#
if format == JSONFORMATKEY:
    resultsData.printJSONReport()


#
#   Output CSV format
#
elif format == CSVFORMATKEY:
    resultsData.printCSVReport()

#
#   Output COMP 40 format
#
elif format == COMP40FORMATKEY:
    # Again, this isn't working now for some reason. Will ask Noah
    writeCOMP40Report(resultsData, resultsData.crossTotals, resultsData.failureReasons, resultsData.valgrindResults, progname)
