#!/usr/bin/env python
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
#    NEEDSWORK: should create some way that this can be tailored 
#               to particular assignments.
#    NEEDSWORK: executable not found handled in crosstabs but not main
#               tables, thus shows only in comp 40 format
#        
#     

import argparse, os, sys, json, csv
from collections import OrderedDict

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
                            default=[JSONFORMATKEY])
    parser.add_argument("-progname", nargs=1, help="name of tested program")
    parser.add_argument('testset', help="input testset summary files", nargs="+")
    args = parser.parse_args()
    return parser.parse_args()



#---------------------------------------------------------------
#                   extractSummary
#
#    Given the dictionary form of a single testset execution summary,
#    extract a flat (no substructure) dictionary with key results
#
#    Note that the order of fields in output such as CSV is determined
#    by the order in which the result OrderedDict is updated because it is, well,
#    ordered! Indeed, adding a field to "result" automatically includes it
#    in output formats such as csv and json.
#
#    Also, as a side effect, builds cross reference totals 
#    for failures and valgrind on a per-student basis
#
#    NEEDSWORK: Need logic to catch bad input with something other
#    than random key failuare asserts
#
#    NEESWORK: cross totals structures are something of an afterthought and
#    probably could be more cleanly related to the main tabular infromation.
#---------------------------------------------------------------

def extractSummary(fname, resultsLog):
    result = OrderedDict()
    try:
        result["student"] = resultsLog["details"]["studentuid"]
        result["testset"] = resultsLog["details"]["testsetname"]
        result["testname"] = resultsLog["name"]
        result["description"] = resultsLog["description"]
        result["success"] = resultsLog["success"]
        result["almostsucceeded"] = resultsLog.get("almostsucceeded")
        result["reason"] = resultsLog["reason"]
        # Only record almost succeeded if true
        if resultsLog.get("almostsucceeded"):
            result["almostsucceeded"] = resultsLog["almostsucceeded"]
        result["testeruid"] = resultsLog["details"]["testeruid"]
        valG = resultsLog.get("valgrind", None)
        if valG:
            result["valgrinderrors"] = valG["Errors"]
            result["valgrinddefinitelylost"] = valG["DefinitelyLostBytes"]
            result["valgrindstillreachable"] = valG["StillReachableBytes"]
            result["valgrindheapinuse"] = valG["HeapInUseBytes"]
        else:
            result["valgrinderrors"] = NOVALGRIND
            result["valgrinddefinitelylost"] = NOVALGRIND
            result["valgrindstillreachable"] = NOVALGRIND
            result["valgrindheapinuse"] = NOVALGRIND

        addCrossTotal(resultsLog, result)
        
    except KeyError as e:
        try:
            print >> sys.stderr, "Could not access key %s in report for Testset: %s Testname: %s Student %s" % (e, result['testset'], result['testname'], result['student'] )
            print >> sys.stderr, "...Check results summary in file: %s" % fname
            print >> sys.stderr, "...Does the testcase correctly check for missingexecutable and timedout before testing execution results?"

            sys.exit(1)
        except KeyError as e2:
            raise

    return result


#---------------------------------------------------------------
#                     addFailureReasons
#
# Count occurrences of each failure message for each student
#---------------------------------------------------------------

def addFailureReason(failureReasons, reason):
    if reason in failureReasons:
        failureReasons[reason] += 1
    else:
        failureReasons[reason] = 1
        

#---------------------------------------------------------------
#                     addValgrindResult
#
# Count occurrences of each non-zero valgrind problem
#
# NOTE: Valgrind itself tends to report numbers of bytes, e.g.
#       lost on the heap. Here we count the number of test cases
#       cases in which a certain type of loss happened.
#---------------------------------------------------------------

def addValgrindResult(valgrindResults, valgrindResult):
    if valgrindResult in valgrindResults:
        valgrindResults[valgrindResult] += 1
    else:
        valgrindResults[valgrindResult] = 1
        

#---------------------------------------------------------------
#                     addCrossTotals
#
# Organize failure-related information by student
# (Note that not all reports depend on this cross-referenced
# representation, but the comp40 format, e.g., does.
#
# Note that this updates the three global(!?!) global dictionaries
# declared below. Each has student login as its key.
#---------------------------------------------------------------
crossTotals = {}                        # key is student login
failureReasons = {}                     # key is student login
valgrindResults = {}                    # key is student login

def addCrossTotal(t, result):

    #
    #  Get the entries in each dictionary for this student, creating if
    #  necessary. (The logic below presumes that all three are always
    #  created here simultaneously, which is why the if statement tests
    #  only studentin crossTotals).
    #
    student = result["student"]
    if not student in crossTotals:
        crossTotals[student] = {}
        failureReasons[student] = {}
        valgrindResults[student] = {}
    studentResults = crossTotals[student]
    studentFailures = failureReasons[student]
    studentValgrind = valgrindResults[student]

    testset = result["testset"]
    testname = result["testname"]
    description = result["description"]

    #
    # Each of the success, timedout and failed arrays has as its 
    # members (testname, description) tuples
    #
    #   so studentResults[testset]["failed"][2][1] is description
    #   of 3rd failed test
    #
    if not testset in studentResults:
        studentResults[testset] = {"success" : [], "timedout" : [],
                                      "failed" : [], "almostsucceeded" : []}

    #
    # Record success or failure of the testcase. Note that a testcase
    # that times out is never recorded as failing. It MAY be recorded
    # as PASSED, in the unlikely case that the success criteria in the
    # testcase specification allowed a timeout
    #
    testsetResult = studentResults[testset]
    if result["success"] == "PASSED":
        testsetResult["success"].append((testname, description))
    elif "executionsummary" in t and "timedout" in t["executionsummary"]:
        testsetResult["timedout"].append((testname, description))
    else:
        if "executionsummary" in t and \
                "execution_failed" in t["executionsummary"] and\
                "executablenotfound" in t["executionsummary"]["execution_failed"]:
            addFailureReason(studentFailures, "Program executable not found")
        else:
            addFailureReason(studentFailures, result["reason"])
        testsetResult["failed"].append((testname, description))
        # Following tests membership and truthiness of almostsucceeded
        if result.get("almostsucceeded"):
            testsetResult["almostsucceeded"].append((testname, description))            


    #
    # If valgrind results were logged, record them.
    # We record only the most important failure for each test
    # (in order: errors, definitely lost, heap in use, then still reachable
    # 
    # Assumption: if valgrinderrors is not present and an integer, valgrind
    # was not run at all and no report should be created
    #
    # NEEDSWORK: Names of variables and keys relating to valgrind data
    #            should be made consistent and simpler
    #
    valgrindErrors = result.get("valgrinderrors", None)
    valgrindDefinitelyLost = result.get("valgrinddefinitelylost", None)
    valgrindHeapInUse = result.get("valgrindheapinuse", None)
    valgrindStillReachable = result.get("valgrindstillreachable", None)
    
    (testname, valgrindErrors, valgrindDefinitelyLost, valgrindHeapInUse, \
        valgrindStillReachable)
    if isinstance( valgrindErrors, int ):   # If valgrind run at all
        if valgrindErrors > 0:
            addValgrindResult(studentValgrind, "Errors")

        elif isinstance( valgrindDefinitelyLost, int ) and valgrindDefinitelyLost > 0:
            addValgrindResult(studentValgrind, "DefinitelyLost")

        elif isinstance( valgrindHeapInUse, int ) and valgrindHeapInUse > 0:
            addValgrindResult(studentValgrind, "HeapInUse")

        elif isinstance( valgrindStillReachable, int ) and valgrindStillReachable > 0:
            addValgrindResult(studentValgrind, "StillReachable")
        else:
            addValgrindResult(studentValgrind, "Passed")


#---------------------------------------------------------------
#                   writeCOMP40Report
#---------------------------------------------------------------

def writeCOMP40Report(resultsData, cross, failureReasons, valgrindResults, progname):
    #
    #   Write required COMP 40 preamble
    #
    #print "utln %s\n" % resultsData[0]["testset"]
    
    for student in sorted(cross.keys()):
        #
        # Initialize and write preamble for student
        #
        groupTotals = crossTotals[student]
        valgrindTotals = valgrindResults[student]
       # print student+"   I"

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
            print ("    Results of testing your {} progam:\n".format(progname))
            

        #
        #   Write one line report on each test set
        #
        for testset in groupTotals:
            testsetData = groupTotals[testset]
            numTests = len(testsetData["success"]) + len(testsetData["timedout"]) + \
                len(testsetData["failed"]) 
            almostCount = len(testsetData["almostsucceeded"])
            print("\nPassed: {}, Failed: {}, Timed out: {}".format(len(testsetData["success"]), len(testsetData["failed"]), len(testsetData["timedout"])))

            # print ("\nPassed %d, " + "Failed %d%s, " + "Timed out %d") % \
            #       (len(testsetData["success"]), \
            #        len(testsetData["failed"]), \
            #        (" (almost passed %d)" % almostCount) if almostCount>0 else "",\
            #        len(testsetData["timedout"]))
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
    
            
        print("\n")

    #
    #   Write required COMP 40 suffix
    #
    #print "<utln-names"
            
 

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


for testsetfilename in args.testset:
    assert os.path.isfile(testsetfilename) and os.access(testsetfilename, os.R_OK), \
        "File %s does not exists or is not readable" % testsetfilename


# - - - - - - - - - - - - - - - - - - - - - - - - 
#   Gather data from input files
# - - - - - - - - - - - - - - - - - - - - - - - - 
resultsData = []
for testsetfilename in args.testset:
    with open(testsetfilename, "r") as testsetfile:
        testsetJSON = json.loads(testsetfile.read())
        resultsData.append(extractSummary(testsetfilename, testsetJSON))


# - - - - - - - - - - - - - - - - - - - - - - - - 
#       Generate output in the format requested
#       by the caller
# - - - - - - - - - - - - - - - - - - - - - - - - 

#
#   Output JSON format
#
if format == JSONFORMATKEY:
    print (json.dumps(resultsData, indent=2, separators=(',', ': ')))

#
#   Output CSV format
#
elif format == CSVFORMATKEY:
    if len(resultsData) > 0:
        csvwriter = csv.DictWriter(sys.stdout,resultsData[0].keys())
        csvwriter.writeheader()
        csvwriter.writerows(resultsData)

#
#   Output COMP 40 format
#
elif format == COMP40FORMATKEY:
    writeCOMP40Report(resultsData, crossTotals, failureReasons, valgrindResults, progname)
