#!/usr/sup/bin/python
# NEEDSWORK: above should be /bin/env python3 (Noah 12/29/2020)
#
#                  test_summary_results.py
#
#        Author: Noah Mendelsohn
#
#    NOTE: as of 1/23/2021 Results3 is a new class that's similar to Results2
#          but with a cleaner interface. The primary change is that all
#          subsets, such as byStudent, are now in sets of indices that can 
#          be manipulated with set operations.
#    
#    NOTE: as of 1/21/2021 Results2 is a new class that's similar to results
#          but with a cleaner interface. The old one is kept for compatibility
#          with old report writers.
#    
#    This class represents the combined information from a number of 
#    test_summaries/<testname>.summary.json files, I.e. the information
#    needed for a results report. Indeed, this code was factored out
#    by Noah as a separate source file implementing the test_summary_results.results
#    class in January of 20201.
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

import argparse, os, sys, json, csv, os.path
import hook
from collections import OrderedDict

NOVALGRIND = "VALGRINDNOTRUN"      # marker value in output for when valgrind not run

#
#   Format names for use with command line -format argument
#
JSONFORMATKEY = 'json'
CSVFORMATKEY = 'csv'
COMP40FORMATKEY = 'comp40'

#************************************************************************
#
#                            Class Results3
#
#     This holds all the results as well as the byStudent.
#
#     NEEDSWORK: Results3 does not support AlmostSucceeded. Results still does.
#     NEEDSWORK: Results3 JSON report is not really JSON at the moment, 
#                has become a debug report in nearly json form for now.
#
#     Note that self.byStudent, self.failureReasons, self.valgrindResults
#     and self.resultsData are effectively public and can be accessed
#     directoy in report writers.
#
#     An instance of this class cast to list() will be a list of
#     the results data.
#
#     Public methods:
#
#         init (constructor): pass in filenames of json filenames and/or dict or dicts
#
#************************************************************************

# The name of the key we add to every results entry giving it's index in the 
# results array. We use these effectively as pointers from the cross totals
# to the results info

INDEX_KEY = "_INDX"

#
#                      ResultsSubset
#     A subset of the results is represented by a predicate
#     and a set. If any member of the Results is known to match
#     the predicate, then the corresponding INDEX_KEY is added to the set.
#
#     For brevity, the both the function members and the attribute m
#     both reference the members set, which can then be used in 
#     set operations like union and intersection.
#
#        e.g. someResultsSet.m & otherResultSet.m (members of both sets)
#
#     Iteration returns members of the set (iterator on the set)
#
#     Note the difference between:
#
#          members (or m):   which is a set of indices which can be intersected etc
#          results():        which is an iterable of actual results
#

class ResultsSubset:
    def __init__(self, debug_string, results_list, pred):
        self.debug_string = debug_string
        self.results_list = results_list # the array of all results
        self.predicate = pred
        self.m = set()                # Set of INDEX_KEYS for members

    def pred(self):
        return self.pred
        
    def members(self):
        return self.members

    #
    #  Adds a member to the appropriate set in the appropriate group
    #  (these are sets, so inserting an existing item does nothing)
    #
    def add(self, r):
        if self.predicate(r):
            self.m.add(r[INDEX_KEY])
            
    #
    #  Iteration goes through the members
    #
    def __iter__(self):
        return iter(self.members())

    #
    # results
    #
    def results(self):
        return (self.results_list[indx] for indx in self.m)
        
        
    #
    #  __repr__
    #
    def __repr__(self):
        return "Results Subset: {{ {} }}".format(repr(list(self.m)))
#
#                      GroupedResultsSubsets
#
#     Basically a dictionary of ResultSubsets, this takes instead of 
#     a predicate a function that, when applied to an individual result
#     entry, returns the key of the subset to which this belongs.
#
#     For example, if the function is: lambda r:r["student"] then the
#     result of inserting a number of results will be to create a subset
#     for each student, with that student's results.
#
#     On the initializer, a grouping function and a predicate are required:
#     The grouping function returns the key value used to partition the set
#
#          grs = GroupedResultsSubset(lambda r: r["student"])
#
#

class GroupedResultsSubsets:
    def __init__(self, debug_string, results_list, groupingFunction):
        self.debug_string = debug_string
        self.results_list = results_list    # the main list of results to which this applies
        self.groupingFunction = groupingFunction
        self.groups = {}           # Key will be values of the grouping function
                              # as applied to individual results

    def groupingFunction(self):
        return self.groupingFunction

    def add(self, result):
#        print("GRS({}).add(repr({})".format(self.debug_string, repr(result)))
        keys = self.groupingFunction(result)
        # keys can be a single string number or bool or a list of them . Turn singleton
        # into tuple with one item 
        # For each key for whick this is to be added, create a subset
        # for that key (if not already created), and add this result
        singleton = False
        if isinstance(keys, str) or isinstance(keys, bool) or isinstance(keys,int) \
           or isinstance(keys, float):
            singleton = True
            keys = [keys]    
        for key in keys:
            #  The result subset predicate will match on this particular key
            resultSubset = self.groups.get(key, 
            ResultsSubset("RS_{}".format(key),
                          self.results_list, 
                          lambda r: (self.groupingFunction(r) == key) if singleton else (key in self.groupingFunction(r))))
            self.groups[key] = resultSubset  # in case it's new
            resultSubset.add(result)
#            print("GRS added to key: {} RS: {{ {} }}".format(key, repr(resultSubset)))
        
    def members(self):
        return self.members
        
    def __repr__(self):
        result = "GroupedResultsSubsets: len={}".format(len(self.groups))
        for k,v in self.groups.items():
            result += "{{key: {} set={} }}".format(k, repr(v))
        return result
            

# Helper function for BUILT_IN_SUBSETS list    
def hasTimedout(r):
    return "timedout" in r

class Results3:
    _BUILT_IN_SUBSETS = (
        ("successful", lambda r: r["success"] == "PASSED"),
        ("failed", lambda r: r["success" != "PASSED"),
         ("timedout", hasTimedout),
         # key is is reason
     )
    
    _BUILT_IN_GROUPED_SUBSETS = (
        # key is student login
        ("byStudent", lambda r: r["student"]),
        # key is testset       
        ("byTestset", lambda r: r["testset"]),
        # key is is success
        ("bySuccess", lambda r: r["success"]),
        # key is is reason
        ("byReason", lambda r: r["reason"]),
        # timed out (this is ALWAYS a subset of bySuccess != SUCCESS
        ("byTimedout", getTimeout),
        # byCategory: note categories really is plural. If a result
        # is in multiple categories it will be filed under each
        ("byCategory", lambda r: (r["categories"] if ("categories" in r) else Tuple()))
    )
    
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #                 Constructor
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self, files=None, dict=None, dicts=None ):   # NEEDSWORK
#        print("In RESULTS constructor\nfiles={} dict={} dicts={}".format(
#            files, dict, dicts), file=sys.stderr)
        assert not (dict and dicts), "Class Results3: constructor wants dict or dicts, not both"

        # All of the data with one row per summary JSON file
        self.resultsData = []                        # list of orderedDicts
                                                     # from extractSummary

        # counts of failure reasons, valgrind errors
        self.byStudentData = {}

        #
        # Before we extract the data, define all the subsets and grouped subsets
        # into which we will categorize these
        #
        #  Note that for a subset defined as ("byStudent", ...some lambda or func...)
        #  the following code adds an attribute byStudent to this Results3 object.
        #  So, if we have:
        #
        #   r = Results3(file=some_files ....)
        #   bobsubs =r.byStudent["bob'] #is the resultsSubset for submissions from bob
        #
        self.subsetNames = []          # list of subset names we build below
        for subsetName, subsetFunction in self._BUILT_IN_SUBSETS:
            self.addSubset(subsetName, subsetFunction)

        self.groupedSubsetNames = []          # list of subset names we build below
        for subsetName, subsetFunction in self._BUILT_IN_GROUPED_SUBSETS:
            self.addGroupedSubset(subsetName, subsetFunction)

        #
        # If files supplied, add data from them
        #
        if files:
            for summaryFilename in files:
                assert os.path.isfile(summaryFilename) and os.access(summaryFilename, os.R_OK), \
                    "File %s does not exists or is not readable" % summaryFilename

            for summaryFilename in files:
                self.extractFromJSONFile(summaryFilename)

        #
        # Handle single dict
        #
        if dict:
            dicts = [dict]
        
        #
        # add data from supplied dicts
        #
        if dicts:
            for d in dicts:
                self.extractFromDict(d)
#        print("Leaving RESULTS constructor", file=sys.stderr)

    #
    #                    add
    #
    #    Add a new result item to results.data, updating all subsets
    #
    def add(self, r):
#        print("RESULTS.ADD: len(self.subsetNames)={}".format(len(self.subsetNames)))
        r[INDEX_KEY] = len(self.resultsData)    # new items get next index
        self.resultsData.append(r)              # add to the main results list
        #
        #  Update each grouped subset to track new item
        #
        for subsetName in [self.groupedSubsetNames + self.subsetNames]:
            subset = getattr(self, subsetName)  # the instance of the 
                                                # GroupedResultsSubset or resultsSubset class
#            if r["testname"] == "digits_123" and r["student"] == "crashloop":
#                print("DIGITS 123 added subset=" + subset.debug_string + "  || " + repr(subset))
#                print("DIGITS RESULT: " + json.dumps(r, indent=2, separators=(',', ': ')))
            subset.add(r)                                    

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #                   addSubset
    #
    #        Adds a subset that we will manage
    #
    #        The first time this is called from init we have
    #        no results anyway, but users might add subsets
    #        later, in which case we need to put all the existing results
    #        in the subsets.
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def addSubset(self,subsetName,subsetFunction):
        #
        #  Create a new ResultsSubset and make it accessible
        #  as an attribute of this Results3 object
        #
        rs = resultsSubsets(subsetName, self.resultsData, subsetFunction)
        setattr(self, subsetName, rs)
        self.subsetNames.append(subsetName)

        #
        # Go through all results adding to the subset as needed
        #
        for r in self.resultsData:
            rs.add(r)
        
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #      If Results3 object is indexed, iterated or 
    #      converted to list, you get self.resultsData
    #
    #      This makes the new class largely polymorpic with 
    #      the old non-class based versions.
    #
    #      Furthermore, becuase Results3 uses these same indices
    #      to refer to a result, r[ref] does the right thing where
    #      r is a Results3 object
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    #
    #     Instances of this class can be subscripted and iterated
    #     to return results data. This means that dict(Results3 instance) gets
    #     you a copy of the resultsData!
    #

    def __getitem__(self, x):
        return self.resultsData[x]

    def __len__(self):
        return len(self.resultsData)

    def __iter(self):
        return iter(self.resultsData)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #                 Methods to write reports
    #
    #    These take open output files, not filenames.
    #    The files are not closed at completion
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def printJSONReport(self, file=sys.stdout):
        print("Results3 JSON Report")
        print("{\"resultsData\" : { %s }, \"byStudentData\" : { %s } }" % (json.dumps(list(self.resultsData), indent=2, separators=(',', ': ')), json.dumps(self.byStudentData, indent=2, separators=(',', ': '))),
              file=file)
        print("Subset names: " + repr(self.subsetNames))
        print("byStudent Set", repr(self.byStudent))
        print("bySuccess Set", repr(self.bySuccess))
        print("byReason Set", repr(self.byReason))
        print("byTimedout Set", repr(self.byTimedout))
        print("byCategory Set", repr(self.byCategory))
        

    def printCSVReport(self, file=sys.stdout):
        resultsData = self.resultsData
        if len(resultsData) > 0:
            csvwriter = csv.DictWriter(file,resultsData[0].keys())
            csvwriter.writeheader()
            csvwriter.writerows(list(resultsData))




    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #      Methods to assemble and cross reference
    #      the summary data
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    #  Add to results data and cross totals from a JSON file
    #

    def extractFromJSONFile(self,summaryFilename):
        # - - - - - - - - - - - - - - - - - - - - - - - - 
        #   Gather data from input files
        # - - - - - - - - - - - - - - - - - - - - - - - - 
        with open(summaryFilename, "r", newline="", encoding="ascii") as summaryFile:
            summaryJSON = json.loads(summaryFile.read())
            self.extractFromDict(summaryJSON, summaryFilename=summaryFilename)

    #
    #  Add to results data and cross totals from a dict
    #

    def extractFromDict(self, input_data, summaryFilename="Not from file"):
        # In addition to the summary data, we are going to add a key _ResultsIndex
        # that is the index you would get if you enumerated results
        # We use this as effectively a pointer in other places where we 
        # would need to reference a results entry (typically from
        # something in byStudentData
        indx = len(self.resultsData)
        # extract_summary needs the index so we put it in the data before calling
        self.add(self.extractSummary(summaryFilename, input_data, indx))



    #---------------------------------------------------------------
    #                   extractSummary
    #
    #    Given the dictionary form of a single testset execution summary,
    #    dictionary with important results. (Noah changed this comment on 1/2/2021:
    #    it used to promise that results would be a dict with no substructure, 
    #    but for years fields like details and execution summary have been nested.)
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
    #    NOTE: fname is used only to make error messages more useful
    #          This method does not read files.
    #---------------------------------------------------------------

    def extractSummary(self, fname, resultsLog, indx):
        result = OrderedDict()
        try:
            # DEBUG PRINTING
#            print("In extract summary, fname {} resultsLog = {}".format(fname, 
#                                                                        repr(resultsLog)),
#                  file=sys.stderr)
            result[INDEX_KEY] = indx
            result["student"] = resultsLog["details"]["studentuid"]
            result["testset"] = resultsLog["details"]["testsetname"]
            result["testname"] = resultsLog["name"]
            result["description"] = resultsLog["description"]
            category = resultsLog.get("category","")
            #
            # We allow properties of category and/or categories, but
            # the summary always provides a list under categories!
            #
            result["categories"] = resultsLog.get("categories",[])
            if category:
                result["categories"].append(category)
            result["data"] = resultsLog.get("data",None)
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

            self.addByStudent(resultsLog, result)
        
        except KeyError as e:
            try:
                print("extractSummary: exception {} in fname {}".format(e, fname))
                print("Could not access key {} in report for Testset: {} Testname: {} Student {}".format(e, result['testset'], result['testname'], result['student']),
                file=sys.stderr)
                print("...Check results summary in file: {}".format(fname), file=sys.stderr)
                print("...Does the testcase correctly check for missingexecutable and timedout before testing execution results?", file=sys.stderr)
                raise e

                sys.exit(1)
            except KeyError as e2:
                raise

        return result


    #---------------------------------------------------------------
    #                     addFailureReasons
    #
    # Count occurrences of each failure message for each student
    #
    #   NEEDSWORK:
    #   WARNING: ON 1/10/2021 NOAH FOUND AND "FIXED" WHAT APPEARED
    #   TO HAVE BEEN A LONG STANDING BUT IN WHICH THIS CODE WAS
    #   UPDATING self.failureReaons INSTEAD OF failureReasons. 
    #   NOT CLEAR HOW IT EVER WORKED BUT HE'S NERVOUS THAT HE MISSED
    #   SOMETHING AND MAY HAVE BROKEN OLDER TESTSETS.
    #
    #---------------------------------------------------------------

    def addFailureReason(self, failureReasons, reason):
        if reason in failureReasons:
            failureReasons[reason] += 1
        else:
            failureReasons[reason] = 1
        

    #---------------------------------------------------------------
    #                     addValgrindResult
    #
    # Count occurrences of each non-zero valgrind problem
    #
    #   NEEDSWORK:
    #   WARNING: ON 1/10/2021 NOAH FOUND AND "FIXED" WHAT APPEARED
    #   TO HAVE BEEN A LONG STANDING BUT IN WHICH THIS CODE WAS
    #   UPDATING self.valgrindResults INSTEAD OF valgrindResults. 
    #   NOT CLEAR HOW IT EVER WORKED BUT HE'S NERVOUS THAT HE MISSED
    #   SOMETHING AND MAY HAVE BROKEN OLDER TESTSETS.
    #
    # NOTE: Valgrind itself tends to report numbers of bytes, e.g.
    #       lost on the heap. Here we count the number of test cases
    #       cases in which a certain type of loss happened.
    #---------------------------------------------------------------

    def addValgrindResult(self, valgrindResults, valgrindResult):
        if valgrindResult in valgrindResults:
            valgrindResults[valgrindResult] += 1
        else:
            valgrindResults[valgrindResult] = 1
        

    #---------------------------------------------------------------
    #                     addByStudents
    #
    # Organize failure-related information by student
    # (Note that not all reports depend on this cross-referenced
    # representation, but the comp40 format, e.g., does.
    #
    #  This is called once per results, so the student involved is
    #  extraced from that result.
    #
    #---------------------------------------------------------------

    def addByStudent(self, t, result):

        #
        #  Get the entries in each dictionary for this student, creating if
        #  necessary. (The logic below presumes that all three are always
        #  created here simultaneously, which is why the if statement tests
        #  only studentin byStudentData).
        #
        student = result["student"]                   # student for whom new data has arrived
        if not student in self.byStudentData:
            self.byStudentData[student]= {"failureReasons" : {}, "valgrindResults" : {}}

        studentResults = self.byStudentData[student]
        studentFailures = studentResults["failureReasons"]
        studentValgrind = studentResults["valgrindResults"]
                            
        testset = result["testset"]
        testname = result["testname"]
        description = result["description"]
        resultIndex = result[INDEX_KEY]         # Index in the resultsData of this result

        #
        # Record success or failure of the testcase. 
        #
        # Specifically: 
        #    1) Update testsetResult["success"/"timedout"/"failed"] the
        #       index of the result in questions 
        #    2) Update in the studentFailures dictionary for each failure
        #       reasons, a count of the number of times that failure occurred.
        #       I.e. the failure strings like "Program executable not found" are
        #       the keys, and the values are counts
        #
        # Note that a testcase
        # that times out is never recorded as failing. It MAY be recorded
        # as PASSED, in the unlikely case that the success criteria in the
        # testcase specification allowed a timeout
        #
        if (result["success"] != "PASSED") and \
            "executionsummary" in t and "timedout" in t["executionsummary"]:
            # new in Result3, timedout becomes a key in result with boolean
            # value. Note that timedout is always a subset of suceess==FAILED
            result["timedout"] = True
            self.byTimedout.add(result)
        else:
            #
            # The following if statement records in "studentFailures" the
            # number of counts for each reason string. So, the keys are the
            # strings and addFailureReason updates the counts (e.g. of the
            # number of times that the Program executable could not be found)
            #
            if "executionsummary" in t and \
               "execution_failed" in t["executionsummary"] and\
               "executablenotfound" in t["executionsummary"]["execution_failed"]:
                self.addFailureReason(studentFailures, "Program executable not found")
            else:
                self.addFailureReason(studentFailures, result["reason"])
                # Following tests membership and truthiness of almostsucceeded
                # NEEDSWORK: Results3 does not support almostsucceeded
                # if result.get("almostsucceeded"):
                #    testsetResult["almostsucceeded"].append(resultIndex)            


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
    
        #
        # Noah thinks the following two lines were accidentally uncommented
        # by Richard, as they appear in Noah's master version with a comment
        # saying, basically "what's this?"
        #
        #(testname, valgrindErrors, valgrindDefinitelyLost, valgrindHeapInUse, \
        # valgrindStillReachable)

        #
        #  Update Valgrind totals, if any
        #
        if isinstance( valgrindErrors, int ):   # If valgrind run at all
            if valgrindErrors > 0:
                self.addValgrindResult(studentValgrind, "Errors")

            elif isinstance( valgrindDefinitelyLost, int ) and valgrindDefinitelyLost > 0:
                self.addValgrindResult(studentValgrind, "DefinitelyLost")

            elif isinstance( valgrindHeapInUse, int ) and valgrindHeapInUse > 0:
                self.addValgrindResult(studentValgrind, "HeapInUse")

            elif isinstance( valgrindStillReachable, int ) and valgrindStillReachable > 0:
                self.addValgrindResult(studentValgrind, "StillReachable")
            else:
                self.addValgrindResult(studentValgrind, "Passed")
            

#************************************************************************
#
#                            Class Results2
#
#     This holds all the results as well as the byStudent.
#
#     Note that self.byStudent, self.failureReasons, self.valgrindResults
#     and self.resultsData are effectively public and can be accessed
#     directoy in report writers.
#
#     An instance of this class cast to list() will be a list of
#     the results data.
#
#     Public methods:
#
#         init (constructor): pass in filenames of json filenames and/or dict or dicts
#
#************************************************************************

# The name of the key we add to every results entry giving it's index in the 
# results array. We use these effectively as pointers from the cross totals
# to the results info

INDEX_KEY = "_INDX"

class Results2:
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #                 Constructor
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self, files=None, dict=None, dicts=None ):   # NEEDSWORK
#        print("In RESULTS constructor\nfiles={} dict={} dicts={}".format(
#            files, dict, dicts), file=sys.stderr)
        assert not (dict and dicts), "Class Results2: constructor wants dict or dicts, not both"

        # All of the data with one row per summary JSON file
        self.resultsData = []                        # list of orderedDicts
                                                     # from extractSummary
        # Interesting data organized by student login
        self.byStudentData = {}                          # key is student login
                      
        #
        # If files supplied, add data from them
        #
        if files:
            for summaryFilename in files:
                assert os.path.isfile(summaryFilename) and os.access(summaryFilename, os.R_OK), \
                    "File %s does not exists or is not readable" % summaryFilename

            for summaryFilename in files:
                self.extractFromJSONFile(summaryFilename)

        #
        # Handle single dict
        #
        if dict:
            dicts = [dict]
        
        #
        # add data from supplied dicts
        #
        if dicts:
            for d in dicts:
                self.extractFromDict(d)
#        print("Leaving RESULTS constructor", file=sys.stderr)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #      If Results2 object is indexed, iterated or 
    #      converted to list, you get self.resultsData
    #
    #      This makes the new class largely polymorpic with 
    #      the old non-class based versions.
    #
    #      Furthermore, becuase Results2 uses these same indices
    #      to refer to a result, r[ref] does the right thing where
    #      r is a results2 object
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    #
    #     Instances of this class can be subscripted and iterated
    #     to return results data. This means that dict(Results2 instance) gets
    #     you a copy of the resultsData!
    #

    def __getitem__(self, x):
        return self.resultsData[x]

    def __len__(self):
        return len(self.resultsData)

    def __iter(self):
        return iter(self.resultsData)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #                 Methods to write reports
    #
    #    These take open output files, not filenames.
    #    The files are not closed at completion
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def printJSONReport(self, file=sys.stdout):
        print("{\"resultsData\" : { %s }, \"byStudentData\" : { %s } }" % (json.dumps(list(self.resultsData), indent=2, separators=(',', ': ')), json.dumps(self.byStudentData, indent=2, separators=(',', ': '))),
              file=file)

    def printCSVReport(self, file=sys.stdout):
        resultsData = self.resultsData
        if len(resultsData) > 0:
            csvwriter = csv.DictWriter(file,resultsData[0].keys())
            csvwriter.writeheader()
            csvwriter.writerows(list(resultsData))




    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #      Methods to assemble and cross reference
    #      the summary data
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    #  Add to results data and cross totals from a JSON file
    #

    def extractFromJSONFile(self,summaryFilename):
        # - - - - - - - - - - - - - - - - - - - - - - - - 
        #   Gather data from input files
        # - - - - - - - - - - - - - - - - - - - - - - - - 
        with open(summaryFilename, "r", newline="", encoding="ascii") as summaryFile:
            summaryJSON = json.loads(summaryFile.read())
            self.extractFromDict(summaryJSON, summaryFilename=summaryFilename)

    #
    #  Add to results data and cross totals from a dict
    #

    def extractFromDict(self, input_data, summaryFilename="Not from file"):
        # In addition to the summary data, we are going to add a key _ResultsIndex
        # that is the index you would get if you enumerated results
        # We use this as effectively a pointer in other places where we 
        # would need to reference a results entry (typically from
        # something in byStudentData
        indx = len(self.resultsData)
        # extract_summary needs the index so we put it in the data before calling
        self.resultsData.append(self.extractSummary(summaryFilename, input_data, indx))



    #---------------------------------------------------------------
    #                   extractSummary
    #
    #    Given the dictionary form of a single testset execution summary,
    #    dictionary with important results. (Noah changed this comment on 1/2/2021:
    #    it used to promise that results would be a dict with no substructure, 
    #    but for years fields like details and execution summary have been nested.)
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
    #    NOTE: fname is used only to make error messages more useful
    #          This method does not read files.
    #---------------------------------------------------------------

    def extractSummary(self, fname, resultsLog, indx):
        result = OrderedDict()
        try:
            # DEBUG PRINTING
#            print("In extract summary, fname {} resultsLog = {}".format(fname, 
#                                                                        repr(resultsLog)),
#                  file=sys.stderr)
            result[INDEX_KEY] = indx
            result["student"] = resultsLog["details"]["studentuid"]
            result["testset"] = resultsLog["details"]["testsetname"]
            result["testname"] = resultsLog["name"]
            result["description"] = resultsLog["description"]
            category = resultsLog.get("category","")
            #
            # We allow properties of category and/or categories, but
            # the summary always provides a list under categories!
            #
            result["categories"] = resultsLog.get("categories",[])
            if category:
                result["categories"].append(category)
            result["data"] = resultsLog.get("data",None)
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

            self.addByStudent(resultsLog, result)
        
        except KeyError as e:
            try:
                print("extractSummary: exception {} in fname {}".format(e, fname))
                print("Could not access key {} in report for Testset: {} Testname: {} Student {}".format(e, result['testset'], result['testname'], result['student']),
                file=sys.stderr)
                print("...Check results summary in file: {}".format(fname), file=sys.stderr)
                print("...Does the testcase correctly check for missingexecutable and timedout before testing execution results?", file=sys.stderr)
                raise e

                sys.exit(1)
            except KeyError as e2:
                raise

        return result


    #---------------------------------------------------------------
    #                     addFailureReasons
    #
    # Count occurrences of each failure message for each student
    #
    #   NEEDSWORK:
    #   WARNING: ON 1/10/2021 NOAH FOUND AND "FIXED" WHAT APPEARED
    #   TO HAVE BEEN A LONG STANDING BUT IN WHICH THIS CODE WAS
    #   UPDATING self.failureReaons INSTEAD OF failureReasons. 
    #   NOT CLEAR HOW IT EVER WORKED BUT HE'S NERVOUS THAT HE MISSED
    #   SOMETHING AND MAY HAVE BROKEN OLDER TESTSETS.
    #
    #---------------------------------------------------------------

    def addFailureReason(self, failureReasons, reason):
        if reason in failureReasons:
            failureReasons[reason] += 1
        else:
            failureReasons[reason] = 1
        

    #---------------------------------------------------------------
    #                     addValgrindResult
    #
    # Count occurrences of each non-zero valgrind problem
    #
    #   NEEDSWORK:
    #   WARNING: ON 1/10/2021 NOAH FOUND AND "FIXED" WHAT APPEARED
    #   TO HAVE BEEN A LONG STANDING BUT IN WHICH THIS CODE WAS
    #   UPDATING self.valgrindResults INSTEAD OF valgrindResults. 
    #   NOT CLEAR HOW IT EVER WORKED BUT HE'S NERVOUS THAT HE MISSED
    #   SOMETHING AND MAY HAVE BROKEN OLDER TESTSETS.
    #
    # NOTE: Valgrind itself tends to report numbers of bytes, e.g.
    #       lost on the heap. Here we count the number of test cases
    #       cases in which a certain type of loss happened.
    #---------------------------------------------------------------

    def addValgrindResult(self, valgrindResults, valgrindResult):
        if valgrindResult in valgrindResults:
            valgrindResults[valgrindResult] += 1
        else:
            valgrindResults[valgrindResult] = 1
        

    #---------------------------------------------------------------
    #                     addByStudents
    #
    # Organize failure-related information by student
    # (Note that not all reports depend on this cross-referenced
    # representation, but the comp40 format, e.g., does.
    #
    #  This is called once per results, so the student involved is
    #  extraced from that result.
    #
    #---------------------------------------------------------------

    def addByStudent(self, t, result):

        #
        #  Get the entries in each dictionary for this student, creating if
        #  necessary. (The logic below presumes that all three are always
        #  created here simultaneously, which is why the if statement tests
        #  only studentin byStudentData).
        #
        student = result["student"]                   # student for whom new data has arrived
        if not student in self.byStudentData:
            self.byStudentData[student]= {"byTestset" : {}, "failureReasons" : {}, "valgrindResults" : {}}
        studentResults = self.byStudentData[student]
        studentFailures = studentResults["failureReasons"]
        studentValgrind = studentResults["valgrindResults"]
                            
        studentByTestset = studentResults["byTestset"]

        testset = result["testset"]
        testname = result["testname"]
        description = result["description"]
        resultIndex = result[INDEX_KEY]         # Index in the resultsData of this result

        #
        # Each of the success, timedout and failed arrays has as its 
        # members an integer which corresponds to the position of the
        # corresponding result in the resultsData (and thus to its INDEX_KEY
        #
        #
        #   so studentResults[testset]["failed"][2] is the index to the
        #   results entry of the 3rd falied test
        #
        if not testset in studentByTestset:
            studentByTestset[testset] = {"successFailTotals" : {"success" : [], "timedout" : [],
                                       "failed" : [], "almostsucceeded" : []}}

        #
        # Record success or failure of the testcase. 
        #
        # Specifically: 
        #    1) Update testsetResult["success"/"timedout"/"failed"] the
        #       index of the result in questions 
        #    2) Update in the studentFailures dictionary for each failure
        #       reasons, a count of the number of times that failure occurred.
        #       I.e. the failure strings like "Program executable not found" are
        #       the keys, and the values are counts
        #
        # Note that a testcase
        # that times out is never recorded as failing. It MAY be recorded
        # as PASSED, in the unlikely case that the success criteria in the
        # testcase specification allowed a timeout
        #
        testsetResult = studentByTestset[testset]["successFailTotals"]
        if result["success"] == "PASSED":
            testsetResult["success"].append(resultIndex)
        elif "executionsummary" in t and "timedout" in t["executionsummary"]:
            testsetResult["timedout"].append(resultIndex)
        else:
            #
            # The following if statement records in "studentFailures" the
            # number of counts for each reason string. So, the keys are the
            # strings and addFailureReason updates the counts (e.g. of the
            # number of times that the Program executable could not be found)
            #
            if "executionsummary" in t and \
               "execution_failed" in t["executionsummary"] and\
               "executablenotfound" in t["executionsummary"]["execution_failed"]:
                self.addFailureReason(studentFailures, "Program executable not found")
            else:
                self.addFailureReason(studentFailures, result["reason"])
                testsetResult["failed"].append(resultIndex)
                # Following tests membership and truthiness of almostsucceeded
                if result.get("almostsucceeded"):
                    testsetResult["almostsucceeded"].append(resultIndex)            


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
    
        #
        # Noah thinks the following two lines were accidentally uncommented
        # by Richard, as they appear in Noah's master version with a comment
        # saying, basically "what's this?"
        #
        #(testname, valgrindErrors, valgrindDefinitelyLost, valgrindHeapInUse, \
        # valgrindStillReachable)

        #
        #  Update Valgrind totals, if any
        #
        if isinstance( valgrindErrors, int ):   # If valgrind run at all
            if valgrindErrors > 0:
                self.addValgrindResult(studentValgrind, "Errors")

            elif isinstance( valgrindDefinitelyLost, int ) and valgrindDefinitelyLost > 0:
                self.addValgrindResult(studentValgrind, "DefinitelyLost")

            elif isinstance( valgrindHeapInUse, int ) and valgrindHeapInUse > 0:
                self.addValgrindResult(studentValgrind, "HeapInUse")

            elif isinstance( valgrindStillReachable, int ) and valgrindStillReachable > 0:
                self.addValgrindResult(studentValgrind, "StillReachable")
            else:
                self.addValgrindResult(studentValgrind, "Passed")
            

#************************************************************************
#
#                            Class Results
#
#     This holds all the results as well as the crossTotals.
#
#     Note that self.crossTotals, self.failureReasons, self.valgrindResults
#     and self.resultsData are effectively public and can be accessed
#     directoy in report writers.
#
#     An instance of this class cast to list() will be a list of
#     the results data.
#
#     Public methods:
#
#         init (constructor): pass in filenames of json filenames and/or dict or dicts
#
#************************************************************************

class Results:
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #                 Constructor
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self, files=None, dict=None, dicts=None ):   # NEEDSWORK
#        print("In RESULTS constructor\nfiles={} dict={} dicts={}".format(
#            files, dict, dicts), file=sys.stderr)
        assert not (dict and dicts), "Class Results: constructor wants dict or dicts, not both"
        self.crossTotals = {}                        # key is student login
        self.failureReasons = {}                     # key is student login
        self.valgrindResults = {}                    # key is student login
        self.resultsData = []                        # list of orderedDicts
                                                     # from extractSummary

        #
        # If files supplied, add data from them
        #
        if files:
            for summaryFilename in files:
                assert os.path.isfile(summaryFilename) and os.access(summaryFilename, os.R_OK), \
                    "File %s does not exists or is not readable" % summaryFilename

            for summaryFilename in files:
                self.extractFromJSONFile(summaryFilename)

        #
        # Handle single dict
        #
        if dict:
            dicts = [dict]
        
        #
        # add data from supplied dicts
        #
        if dicts:
            for d in dicts:
                self.extractFromDict(d)
#        print("Leaving RESULTS constructor", file=sys.stderr)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #      If Results object is indexed, iterated or 
    #      converted to list, you get self.resultsData
    #
    #      This makes the new class largely polymorpic with 
    #      the old non-class based versions.
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    #
    #     Instances of this class can be subscripted and iterated
    #     to return results data. This means that dict(Results instance) gets
    #     you a copy of the resultsData!
    #

    def __getitem__(self, x):
        return self.resultsData[x]

    def __len__(self):
        return len(self.resultsData)

    def __iter(self):
        return iter(self.resultsData)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #                 Methods to write reports
    #
    #    These take open output files, not filenames.
    #    The files are not closed at completion
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def printJSONReport(self, file=sys.stdout):
        print("{}".format(json.dumps(list(self.resultsData), indent=2, separators=(',', ': '))),
              file=file)

    def printCSVReport(self, file=sys.stdout):
        resultsData = self.resultsData
        if len(resultsData) > 0:
            csvwriter = csv.DictWriter(file,resultsData[0].keys())
            csvwriter.writeheader()
            csvwriter.writerows(list(resultsData))




    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #      Methods to assemble and cross reference
    #      the summary data
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    #  Add to results data and cross totals from a JSON file
    #

    def extractFromJSONFile(self,summaryFilename):
        # - - - - - - - - - - - - - - - - - - - - - - - - 
        #   Gather data from input files
        # - - - - - - - - - - - - - - - - - - - - - - - - 
        with open(summaryFilename, "r", newline="", encoding="ascii") as summaryFile:
            summaryJSON = json.loads(summaryFile.read())
            self.extractFromDict(summaryJSON, summaryFilename=summaryFilename)

    #
    #  Add to results data and cross totals from a dict
    #

    def extractFromDict(self, input_data, summaryFilename="Not from file"):
        self.resultsData.append(self.extractSummary(summaryFilename, input_data))


    #---------------------------------------------------------------
    #                   extractSummary
    #
    #    Given the dictionary form of a single testset execution summary,
    #    dictionary with important results. (Noah changed this comment on 1/2/2021:
    #    it used to promise that results would be a dict with no substructure, 
    #    but for years fields like details and execution summary have been nested.)
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
    #
    #    NOTE: fname is used only to make error messages more useful
    #          This method does not read files.
    #---------------------------------------------------------------

    def extractSummary(self, fname, resultsLog):
        result = OrderedDict()
        try:
            # DEBUG PRINTING
#            print("In extract summary, fname {} resultsLog = {}".format(fname, 
#                                                                        repr(resultsLog)),
#                  file=sys.stderr)
            result["student"] = resultsLog["details"]["studentuid"]
            result["testset"] = resultsLog["details"]["testsetname"]
            result["testname"] = resultsLog["name"]
            result["description"] = resultsLog["description"]
            category = resultsLog.get("category","")
            #
            # We allow properties of category and/or categories, but
            # the summary always provides a list under categories!
            #
            result["categories"] = resultsLog.get("categories",[])
            if category:
                result["categories"].append(category)
            result["data"] = resultsLog.get("data",None)
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

            self.addCrossTotal(resultsLog, result)
        
        except KeyError as e:
            try:
                print("extractSummary: exception {} in fname {}".format(e, fname))
                print("Could not access key {} in report for Testset: {} Testname: {} Student {}".format(e, result['testset'], result['testname'], result['student']),
                file=sys.stderr)
                print("...Check results summary in file: {}".format(fname), file=sys.stderr)
                print("...Does the testcase correctly check for missingexecutable and timedout before testing execution results?", file=sys.stderr)

                sys.exit(1)
            except KeyError as e2:
                raise

        return result


    #---------------------------------------------------------------
    #                     addFailureReasons
    #
    # Count occurrences of each failure message for each student
    #
    #   NEEDSWORK:
    #   WARNING: ON 1/10/2021 NOAH FOUND AND "FIXED" WHAT APPEARED
    #   TO HAVE BEEN A LONG STANDING BUT IN WHICH THIS CODE WAS
    #   UPDATING self.failureReaons INSTEAD OF failureReasons. 
    #   NOT CLEAR HOW IT EVER WORKED BUT HE'S NERVOUS THAT HE MISSED
    #   SOMETHING AND MAY HAVE BROKEN OLDER TESTSETS.
    #
    #---------------------------------------------------------------

    def addFailureReason(self, failureReasons, reason):
        if reason in self.failureReasons:
            failureReasons[reason] += 1
        else:
            failureReasons[reason] = 1
        

    #---------------------------------------------------------------
    #                     addValgrindResult
    #
    # Count occurrences of each non-zero valgrind problem
    #
    #   NEEDSWORK:
    #   WARNING: ON 1/10/2021 NOAH FOUND AND "FIXED" WHAT APPEARED
    #   TO HAVE BEEN A LONG STANDING BUT IN WHICH THIS CODE WAS
    #   UPDATING self.valgrindResults INSTEAD OF valgrindResults. 
    #   NOT CLEAR HOW IT EVER WORKED BUT HE'S NERVOUS THAT HE MISSED
    #   SOMETHING AND MAY HAVE BROKEN OLDER TESTSETS.
    #
    # NOTE: Valgrind itself tends to report numbers of bytes, e.g.
    #       lost on the heap. Here we count the number of test cases
    #       cases in which a certain type of loss happened.
    #---------------------------------------------------------------

    def addValgrindResult(self, valgrindResults, valgrindResult):
        if valgrindResult in self.valgrindResults:
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
    #
    #
    #  This is called once per results, so the student involved is
    #  extraced from that result.
    #
    #---------------------------------------------------------------

    def addCrossTotal(self, t, result):

        #
        #  Get the entries in each dictionary for this student, creating if
        #  necessary. (The logic below presumes that all three are always
        #  created here simultaneously, which is why the if statement tests
        #  only studentin crossTotals).
        #
        student = result["student"]
        if not student in self.crossTotals:
            self.crossTotals[student] = {}
            self.failureReasons[student] = {}
            self.valgrindResults[student] = {}
        studentResults = self.crossTotals[student]
        studentFailures = self.failureReasons[student]
        studentValgrind = self.valgrindResults[student]

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
        # Record success or failure of the testcase. 
        #
        # Specifically: 
        #    1) Update testsetResult["success"/"timedout"/"failed"] with a tuple
        #       of (testname, description)
        #    2) Update in the studentFailures dictionary for each failure
        #       reasons, a count of the number of times that failure occurred.
        #       I.e. the failure strings like "Program executable not found" are
        #       the keys, and the values are counts
        #
        # Note that a testcase
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
            #
            # The following if statement records in "studentFailures" the
            # number of counts for each reason string. So, the keys are the
            # strings and addFailureReason updates the counts (e.g. of the
            # number of times that the Program executable could not be found)
            #
            if "executionsummary" in t and \
               "execution_failed" in t["executionsummary"] and\
               "executablenotfound" in t["executionsummary"]["execution_failed"]:
                self.addFailureReason(studentFailures, "Program executable not found")
            else:
                self.addFailureReason(studentFailures, result["reason"])
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
    
        #
        # Noah thinks the following two lines were accidentally uncommented
        # by Richard, as they appear in Noah's master version with a comment
        # saying, basically "what's this?"
        #
        #(testname, valgrindErrors, valgrindDefinitelyLost, valgrindHeapInUse, \
        # valgrindStillReachable)

        #
        #  Update Valgrind totals, if any
        #
        if isinstance( valgrindErrors, int ):   # If valgrind run at all
            if valgrindErrors > 0:
                self.addValgrindResult(studentValgrind, "Errors")

            elif isinstance( valgrindDefinitelyLost, int ) and valgrindDefinitelyLost > 0:
                self.addValgrindResult(studentValgrind, "DefinitelyLost")

            elif isinstance( valgrindHeapInUse, int ) and valgrindHeapInUse > 0:
                self.addValgrindResult(studentValgrind, "HeapInUse")

            elif isinstance( valgrindStillReachable, int ) and valgrindStillReachable > 0:
                self.addValgrindResult(studentValgrind, "StillReachable")
            else:
                self.addValgrindResult(studentValgrind, "Passed")
            

#---------------------------------------------------------------
#                          Main Test Code
#---------------------------------------------------------------

if __name__ == '__main__':

    #---------------------------------------------------------------
    #                     parseargs
    #
    #    Use Python standard argument parser to parse arguments and provide help
    #---------------------------------------------------------------

    def parseargs():
        parser = argparse.ArgumentParser()
        parser.add_argument('summaries', help="input testset summary files", nargs="+")
        #    args = parser.parse_args()
        parser.add_argument("--version", nargs=1, help="Version of class to build and test", \
                            choices=['v1', 'v2', 'v3'], \
                            default=['v2'])
        parser.add_argument("--format", nargs=1, help="output format", \
                            choices=[JSONFORMATKEY, CSVFORMATKEY, COMP40FORMATKEY], \
                            default=[JSONFORMATKEY])
        return parser.parse_args()




    # - - - - - - - - - - - - - - - - - - - - - - - - 
    #    Parse args and make sure all files are readable before starting
    # - - - - - - - - - - - - - - - - - - - - - - - - 

    args = parseargs()
    format = args.format[0]

    version = args.version[0]

    
    for summaryFilename in args.summaries:
        assert os.path.isfile(summaryFilename) and os.access(summaryFilename, os.R_OK), \
            "File %s does not exists or is not readable" % summaryFilename
                                          

    # - - - - - - - - - - - - - - - - - - - - - - - - 
    #   Gather data from input files
    # - - - - - - - - - - - - - - - - - - - - - - - - 

    assert (version in ("v1", "v2", "v3")),"Invalid version number"

    if version == "v1":
        cls = Results
    elif version == "v2":
        cls = Results2
    elif version == "v3":
        cls = Results3

    resultsData = cls(files=args.summaries)
        
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
