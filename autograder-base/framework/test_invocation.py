#!/usr/sup/bin/python
#
#                  testinvocation.py
#
#        Author: Noah Mendelsohn
#      
#   
#        Classes:
#
#             Test_invocation:   An invocation of a test is a the combination
#                                of a Test (I.e. the specification of a test) and
#                                the parameters needed for a specific run of that
#                                test (e.g. directory of a particular submission
#                                or program to be tested, etc.)
#


# NEEDSWORK: some of these imports not needed after latest code refactor

import os, sys, subprocess, asciijson, re, errno, unixsignals, valgrind, pwd
import json, importlib, traceback

import testcase_exceptions
from testcase_exceptions import TCAssert
from collections import OrderedDict

import hook                                 # local support for dynamic import
import resource                             # set CPU limits, etc.
import signal

from utilities import mkdir, forceRemoveFile  # local wrappers for directory
                                            # creation and file removal

#**********************************************************************
#                          CONSTANTS
#**********************************************************************

rubyMatch = re.compile(r"#{([^}]*)}")       # match a Ruby-style #{....} reference
envMatch = re.compile(r"\$\(([^\)]*)\)")    # match a Makefile-style $(....) reference

CANONICALPACKAGENAME = "canonicalizers"     # name of dir where canonicalizer modules
                                            # are stored within a testset
CANONICALFILEEXTENSION = ".canonical"       # added to get filename of canonical
                                            # form of a results file

FAILEDTOCREATEEXTENSION = ".FAILED"         # extension for files that could
                                            # not be created

DEFAULT_SUMMARIZERNAME = "default"
BUILTIN_SUMMARIZER_MODULE_PREFIX = "builtin.summarizers.testcase"

#**********************************************************************
#                          FUNCTIONS
#**********************************************************************

#-------------------------------------------------------------
#
#                    callStatustoJSON (function)
#
#     Takes an exit rc from subprocess.call and formats it
#     as a JSON string we can write to our test results files
#
#     Note that non-negative rc's are exit codes from the program
#     but negative rc's are what subprocess.call does to reflect
#     death by Unix signal
#-------------------------------------------------------------

def callStatustoJSON(rc):
    if rc >= 0 and rc < 128:
        return "{\"exitCode\" : %d}" %rc
    elif rc >= 128:
        signal = rc - 128
        return unixsignals.toJSON(signal)
    else:
        signal = (-rc)
        return unixsignals.toJSON(signal)



#**********************************************************************
#
#                     Class Test_Invocation
#
#    Represents an individual test to be run. 
#
#    Includes the runTest() method to run the test and
#    summarize the output in the student's test_results directory.
#
#
#     Public Methods:
#
#          Constructor: takes a testcase specification (class Test)
#                       plus properties describing this invocation.
#                       setattr is used to make these true Python attributes
#                       if this object.
#
#
#          runTest: runs the designated test. Stdout and stderr are set
#                   respectively to name.stdout and name.stderr.
#
#          __getattr__: this hook is implemented to make it appear that
#                       all dynamic properties are actual Python attributes.
#                       Specifically, property accesses not satisified by
#                       those added in the constructor are delegated to the
#                       testcase specification object. The net result is
#                       that properties come statically from the testcase
#                       specification (often the testcase.json file) or 
#                       dynamically (directory of the particular program to
#                       be tested). The dynamic override the static.  
#
#          args() - a method returning the arguments to be supplied on the
#                   test as a Python list (note that a default implementation)
#                   is supplied that returns arglist, so if that member is 
#                   set this method can be used.
#
#          DEPRECATED
#
#          The __getattr__ hook is relatively new. To support code that
#          still does it the old way, the following methods provide
#          access to the same properties.
#
#          hasProperty: true iff this test has the named property
#          property:    the value of the property
#
#**********************************************************************

class Test_Invocation(object):

    booleanProperties = ("shell")

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    #               __init__
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __init__(self, test, invocation_properties):
        self.test = test
        self.invocation_property_names = invocation_properties.keys() # used to support the detailed_properties
                                         # iteration in the summarizer
        for item, value in invocation_properties.items():
            # convert boolean invocation_properties to actual True/False
            if item in Test_Invocation.booleanProperties:
                name = invocation_properties.get("name", "NAMENOTYETKNOWN")
                TCAssert((value == "True" or value == "False"), \
                     testcase_exceptions.BadTestcaseSpecification(name, \
                 "Test constructor: property %s must be boolean True or False" % \
                                                                      (item)))
                if value == "True":
                    value = True
                else:
                    value = False
            setattr(self, item, value)

            
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    #             Properties of a test
    #
    #    The hasProperty and property methods are supported for
    #    compatibility with older code that used these methods to
    #    merge properties particular to the invocation with those
    #    of the test itself. In the new architecture, all are 
    #    available as properties of the test_invocation directly
    #    because of the getattr below.
    #
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
            
    def hasProperty(self, prop):
        return hasattr(self, prop) or hasattr(self.test, prop)
    
    def property(self, prop):
        if not self.hasProperty(prop):
            raise testcase_exceptions.TestcasePropertyError(prop)
        return getattr(self, prop) if hasattr(self,prop) else getattr(self.test, prop)

    #
    # make it appear that all attributes of the base test case are attributes
    # of this test_invocation
    #
    def __getattr__(self, name):
        if not hasattr(self.test, name):
            raise AttributeError("Property {} does not exist in Test case attributes or env".format(name))
            #raise testcase_exceptions.TestcasePropertyError(name)            
        return getattr(self.test, name)


    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    #                  args
    #
    #   By wrapping this in a method we can change our
    #   mind someday about how args are encoded
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def args(self):

        TCAssert(hasattr(self, 'arglist'), \
                     testcase_exceptions.BadTestcaseSpecification(self.name, \
                                  "Test.args() called with arglist member undefined"))
        return self.arglist

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    #              filenames for results files
    #
    #      All of these return absolute file paths
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def resultsDirectory(self):
        return os.path.abspath(self.resultscontainerdir)

    def stoutname(self):
        return os.path.join(self.resultsDirectory(), \
                                self.name + '.stdout')

    def sterrname(self):
        return os.path.join(self.resultsDirectory(), \
                                self.name + '.stderr')

    def exitcodefilename(self):
        return os.path.join(self.resultsDirectory(), \
                                self.name + '.exitcode.json')

    def timedoutfilename(self):
        return os.path.join(self.resultsDirectory(), \
                                self.name + '.timedout.json')

    def valgrindlogfilename(self):
        return os.path.join(self.resultsDirectory(), \
                                self.name + '.valgrindlog')

    def valgrindJSONfilename(self):
        return os.path.join(self.resultsDirectory(), \
                                self.name + '.valgrind.json')

    def summaryDirectory(self):
        return os.path.abspath(self.summarycontainerdir)

    def summaryFilename(self):
        if hasattr(self, "summaryfilename"):
            result = getattr(self, "summaryfilename")
            print("In summaryfilename: attribute existed, value={}".format(result))
        else:
            # testsetName/<testname>.summary.json as sibbling of resultsdir
            
            testsetSummaryDir = mkdir(os.path.join(self.summaryDirectory(),
                                                   self.testsetname))
            return os.path.abspath(os.path.join(testsetSummaryDir, \
                                                    self.name + '.summary.json'))


    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    #                expandArgs
    #
    #   Arguments: args is an array of argument strings
    #              env is our usual environment
    #
    #   Return value:
    #              A new array with same values as input, except
    #              escapes below are substituted.
    #
    #   Allows property substitution into the arguments, for the moment
    #   using Ruby #{xxx} syntax where xxx must be the name 
    #   of a property of the test or overridden in the env dictionary.
    #   The syntax $() substitutes Linux environment variable values.
    #
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def expandArgs(self, args):
        def rubySub(t):
            def rubyRepl(s):
                prop = s.group(1)
                try:
                    result = self.property(prop)
                except testcase_exceptions.TestcasePropertyError as e:
                    raise testcase_exceptions.AbandonTestset("expandArgs: property \"%s\" not found" % \
                                             prop)
                return result
            return re.sub(rubyMatch, rubyRepl, t)
        def envSub(t):
            def envRepl(s):
                prop = s.group(1)
                TCAssert(prop in os.environ, \
                             testcase_exceptions.BadTestcaseSpecification(self.name, \
                    "Bad Environmentvar-style property substitution: non-existent property: %s" % prop))
                result = os.environ[prop]
                return result
            return re.sub(envMatch, envRepl, t)
        return map(envSub,map(rubySub, args))
    

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    #                    getSummarizer
    #
    #     CHANGE: Now accepts force_default_summarizer flag to
    #             force loading default. Note that in other cases
    #             you may get the default anyway, so to see if they are both
    #             there you have to try both ways and compare.
    #
    #     Find the summarizer function for this test
    #
    #     NEEDSWORK: ALGORITHM CHANGED 1/4/2021...COMMENTS NEED UPDATING TO REFLECT THAT!
    #     Algorithm:
    #
    #     * If testset specifies successreport/summarizer 
    #       use that, else "default" (DEFAULT_SUMMARIZERNAME)
    #
    #     * Use the hook.load function to load module:
    #       summarizers,testcase.XXX where XXX is from step 1
    #       Note that hook.load will look first in the testsetdir.
    #       When it fails to load, it will try the module:
    #       builtin.summarizers.testcase.XXX, which may well
    #       resolve relative to the bin dir for this test framework
    #       12/30/2020: Noah believes that last bit is wrong...it just
    #       looks for builtin.XXX, where XXX at that point will 
    #       often tend to be DEFAULT_SUMMARIZERNAME (so, typically
    #       we load bin/builtin/summarizers/testcase/default.py)
    #       >>>Although he has yet to test this, he believes that (for 
    #       better or worse, an overriding summarizer would have to be 
    #       in <testsetdir>/summarizers/testcase/<summarizername>.py
    #     
    #     * Note that it's customary for the test framework to
    #       provide a builtin summarizers, which implements 
    #       the predicate language, writes a JSON file, and should
    #       in principle be subclassable by other per-testcase summarizers.
    #
    #     * Within whichever module, the "summarize" function is returned
    #       along with its undefaulted name
    #
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getSummarizer(self, force_default_summarizer = False, fallbackModulePrefix=None):
        #
        # In the following, we raise TestcasePropertyError or KeyError
        # if the testset configuration file doesn't specify summarizer
        #
        if force_default_summarizer:
            summarizer = DEFAULT_SUMMARIZERNAME
        else:
            try:
                successProp = self.successreport
                summarizer = successProp.get("summarizer", DEFAULT_SUMMARIZERNAME)
#                print("getSummarizer: summarizer = {} successprop = {}".format(summarizer, repr(successProp)),file=sys.stderr)
            except testcase_exceptions.TestcasePropertyError as e:
                summarizer = DEFAULT_SUMMARIZERNAME
            except AttributeError as e:
                summarizer = DEFAULT_SUMMARIZERNAME
            except KeyError as e:
                summarizer = DEFAULT_SUMMARIZERNAME
        
        return (hook.load(self.testsetdir, summarizer, "summarize", fallbackModulePrefix=fallbackModulePrefix), "%s" % summarizer)
        
        
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    #                    summarize
    #
    #     Find the summarizer file and use it to create
    #     a summary dictionary object, then serialize
    #     that as JSON.
    #
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def summarize(self):
        
#        print("loading main summarizer", file=sys.stderr)
        summarizeFunction, summarizerModname = self.getSummarizer(force_default_summarizer=False, fallbackModulePrefix = BUILTIN_SUMMARIZER_MODULE_PREFIX)
#        print("loading default summarizer", file=sys.stderr)
        defaultSummarizeFunction, defaultSummarizerModname = self.getSummarizer(force_default_summarizer=True, fallbackModulePrefix = BUILTIN_SUMMARIZER_MODULE_PREFIX)
        assert summarizeFunction or defaultSummarizeFunction, "Could not successfully load summarize function"
        #
        #                 Call the summarizer to do the summary of results
        #
        #  If we are calling a non-default summarizer, then pass in as kwargs
        #  the function and the module name of the default summarizer so that the
        #  non-default one can call the default one if desired.
        #
        if summarizeFunction:
            if (summarizeFunction == defaultSummarizeFunction):
                summary = summarizeFunction(self, self.resultsDirectory())
            else:
                assert defaultSummarizeFunction, "testcase_invocation.py.summarize: could not load default summarizer function for passing to non-default"
                summary = summarizeFunction(self, self.resultsDirectory(), defaultSummarizeFunction=defaultSummarizeFunction, defaultSummarizerModname=defaultSummarizerModname)

        else:
            #
            # Since we couldn't find a summarizer to create a summary report
            # for this testcase, we create one that records the failure
            #
            summary = OrderedDict()
            summary["name"] = self.name
            summary["description"] =  self.description
            summary["success"] =  "FAILED_TO_LOAD_SUMMARIZER"
            summary["reason"] =  "FAILED_TO_LOAD_SUMMARIZER %s" % \
                                 summarizerModname
            summary["details"] =  {
                               "studentdir": self.studentdir,
                               "studentuid": self.studentuid,
                               "testdir": self.testdir,
                               "testeruid": self.testsetname,
                               "testsetdir": self.testsetdir,
                               "testsetname": self.testsetname
                               }

        with open(self.summaryFilename(), "w") as summaryFile:
            summaryFile.write(json.dumps(summary, indent=4, separators=(',', ': ')))
            summaryFile.write("\n")
        

    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    #                    getCanonicalizer
    #
    #     Find the canonicalizer function for this test
    #
    #     We load from module CANONICALPACKAGENAME.mod the named
    #     function
    #
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getCanonicalizer(self, mod, func):
        return hook.load(self.testsetdir, 
                         "%s.%s" % (CANONICALPACKAGENAME, mod), 
                         func)
        
        
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    #                    canonicalFilename
    #
    #     For a given filename, get the name of its canonical form
    #
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def canonicalFilename(self, filename):
        return filename + CANONICALFILEEXTENSION
        
        
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    #                    failedFilename
    #
    #     Sometimes we want to create an output file, such
    #     as a canonicalized version of a file, but we fail.
    #     We need to leave some marker in the test_results
    #     directory. 
    #
    #     This function returns the name of the marker file we
    #     create.
    #
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def failedFilename(self, filename):
        return filename + FAILEDTOCREATEEXTENSION
        
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    #                    failedToCreateFile
    #
    #     Sometimes we want to create an output file, such
    #     as a canonicalized version of a file, but we fail.
    #     We need to leave some marker in the test_results
    #     directory. 
    #
    #     This function leaves such a marker by "touching"
    #     a file with the name filename + FAILEDTOCREATEEXTENSION.
    #
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def failedToCreateFile(self, filename, contents):
        print("failedToCreateFile({}, ENV, {}, {})".format(self.name, filename, contents))
        with open(self.failedFilename(filename), 'w') as f:
            f.write(contents)
        return 

    
        
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    #                    canonicalize:
    #
    #     toConvert is a dict with keys stderr or stdout, and 
    #     values the name of canonicalizer modules to be imported
    #
    #     NEEDSWORK: right now, stdout and stderr are the only supported files
    #
    # - - - - - - - - - - - - - - - - - - - - - - - - - -
 
    def canonicalize(self, toConvert):
        for filename,canonspec in toConvert.items():
            try:
                if not "module" in canonspec:
                    raise testcase_exceptions.BadTestcaseSpecification(self.name,
                               "canonical testcase specifier must supply a module")
                if not "function" in canonspec:
                    raise testcase_exceptions.BadTestcaseSpecification(self.name,
                               "canonical testcase specifier must supply a function")
                canonicalizer = self.getCanonicalizer(canonspec["module"],
                                                 canonspec ["function"])
                if canonicalizer == None:
                    print("Testcase {}: could not load canonicalizer {}.{}".format( \
                        self.name, canonspec["module"],  canonspec ["function"]))
                    raise testcase_exceptions.BadTestcaseSpecification(self.name, \
                        "Could not load canonicalizer %s.%s"  % \
                        (canonspec["module"],  canonspec ["function"]))
                    
                if filename=="stdout":
                    inputfname = self.stoutname()
                elif filename=="stderr":
                    inputfname = self.sterrname()                
                else:
                    print("Unsupported filename to canonicalize {}".format(filename))
                    raise testcase_exceptions.BadTestcaseSpecification(self.name, \
                              "Unsupported filename to canonicalize %s" % filename)
                outputfilename = self.canonicalFilename(inputfname)

                try:
                    canonicalizer(inputfname, outputfilename)
                #NEEDSWORK: NEED A STANDARD FOR WHAT TO LEAVE IN RESULTS
                #           FOR BADFILE (NOT PARSEABLE) ETC.
                # Actually looks like BadFile is not used at all, so
                # commenting it
                except testcase_exceptions.BadFile as e:
                    print("BADFILE: canonicalizing {}".format(inputfname))
                    forceRemoveFile(outputfilename)
                    self.failedToCreateFile(outputfilename, "Exception BADFILE: canonicalizing %s\nReason: %s\n" % (inputfname, e.reason))
                    
                except testcase_exceptions.NoFile as e:
                    print("NOFILE: canonicalizing {}".format(inputfname))
                    forceRemoveFile(outputfilename)
                    self.failedToCreateFile(outputfilename, "Exception NOFILE: canonicalizing %s\n\n%s" % (inputfname, traceback.format_exc()))
                    
            except ImportError as e:
                print("ERROR: testcase.canonicalize for test case {} could not import module {} to get canonicalizer".format(self.name, os.path.join(canonicalizerDirPath, modname)))
                raise testcase_exceptions.BadTestcaseSpecification(self.name, "testcase.canonicalize could not import module %s to get canonicalizer" % (os.path.join(canonicalizerDirPath, modname)))
                                                                   
            


    # - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    #                    runTest
    #
    #   This actually invokes the test causing output
    #   and results summary files to be collected in
    #   the results directory. A summary file named
    #
    #      testname.results.json
    #
    #   Is created by running a summarizer over the results files
    #
    #   NEEDSWORK: env is probably no longer needed as an argument to this method
    #
    # - - - - - - - - - - - - - - - - - - - - - - - - - -

    def runTest(self, env={}):
        self.validateProperties()

        pythonException = None
        try: 
            # - - - - - - - - - - - - - - - - - - - - -
            # Build the argument list to subprocess.call
            # - - - - - - - - - - - - - - - - - - - - -

            localArgs = []

            #
            #  The valgrind property of the test or environment should be
            #  a string like:
            #
            #          "valgrind --leak-check=full"
            #
            #  If missing or empty then leave the arglist empty
            #  for now and go on to add the program name
            #
            if self.hasProperty("valgrind"):
                valgrind_prop = self.valgrind
            else: valgrind_prop = None

            if valgrind_prop != None and valgrind_prop != "":
                valgrindSplit = valgrind_prop.split()

                TCAssert(valgrindSplit[0] == 'valgrind', \
                             testcase_exceptions.BadTestcaseSpecification(self.name, \
                             "Testcase=%s valgrind parameter must begin with token valgrind but is actually \"%s\"" % (self.name, valgrind_prop)))


                valgrindSplit.append("--log-file=%s" % self.valgrindlogfilename())
                localArgs.extend(valgrindSplit)
            else:
                valgrind_prop = None          # Make sure it's not "" for later tests
            
            #
            # Add the program name to the arglist
            # NEEDSWORK: is this mixing of studentdir and programdir right?
            #
#            progdir = env["studentdir"] if "studentdir" in env else self.programdir

            #
            # Changed 1/28/2021 to do avoid doing abspath before substitution of
            # environment vars and properties into program name and path
            # (Noah M.)
            #
            progdir = self.programdir if hasattr(self, 'programdir') else self.studentdir
            progdir = list(self.expandArgs([progdir]))[0]

            progname = self.program
            progname = list(self.expandArgs([progname]))[0]
 
            progname =  os.path.abspath(os.path.join(progdir, progname))

            
            localArgs.extend([ progname ])

            #
            # Add the actual arguments as specified for this test
            #
            localArgs.extend(self.args())

            # - - - - - - - - - - - - - - - - - - - - -
            #   Get names of standard output and error code files
            #   and decide whether this will be run as a shell command
            # - - - - - - - - - - - - - - - - - - - - -


            stoutname = self.stoutname()
            sterrname = self.sterrname()
            valgrindlogfilename = self.valgrindlogfilename()
            exitcodefilename = self.exitcodefilename()
            timedoutfilename = self.timedoutfilename()
            valgrindJSONfilename = self.valgrindJSONfilename()
            rc = 0

            if hasattr(self, 'shell'):
                shellctrl = self.shell
            else:
                shellctrl = False

            # - - - - - - - - - - - - - - - - - - - - -
            #    Do the substitution of #{parm} and 
            #    $(osenvt) vars into the arguments 
            # - - - - - - - - - - - - - - - - - - - - -

            localArgs = self.expandArgs(localArgs)
            #
            # set cpulimit to the CPU limit, if eny,  else None
            #
            if self.hasProperty("cpulimit"):
                cpulimit = self.cpulimit
#                localArgs.insert(0, "catch-signal")
            else:
                cpulimit = None


            # - - - - - - - - - - - - - - - - - - - - -
            #    Run the program to be tested
            # - - - - - - - - - - - - - - - - - - - - -
            foundExecutable = os.path.isfile(progname) and os.access(progname, os.X_OK)
            strerror = None
            if foundExecutable:
                with open(stoutname, "w") as stoutfile:
                    with open(sterrname, "w") as sterrfile:
                        if shellctrl == True:
                            localArgs = ' '.join(localArgs)
        
                        try:
                            #
                            #   Use closure to capture cpulimit in setlimits
                            #
                            def getPreExec():
                                
                                #
                                # Called just before exec() in child process.
                                # Note that we can't usefully set signal handlers
                                # as the child process image is about to be replaced.
                                #
                                def preExec():
                                    # run tests in the student's dir
                                    os.chdir(self.resultsDirectory())

                                    # no core file
                                    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
                                    if cpulimit != None:
                                        # NEEDSWORK: How to allow parent to detect
                                        # death due to excess CPU? 
                                        # if two limits are the same, process will
                                        # die with SIGKILL=9
                                        resource.setrlimit(resource.RLIMIT_CPU, (cpulimit, cpulimit+5))         # NEEDSWORK: make hard limit higher. Norman doesn't change hard
                                return preExec
                                
                            devnull = open(os.devnull, 'r')
                            rc = subprocess.call(localArgs, stdout=stoutfile, \
                                             stdin=devnull, \
                                             stderr=sterrfile, shell=shellctrl, \
                                             preexec_fn = getPreExec());
                        except OSError as e:
                            strerror = e.strerror
                            print("PARENT PROCESS RAISED OSEXCEPTION %s %s".format( \
                                e.strerror, ("for" + e.filename) if (hasattr(e,"filename") and isinstance(e.filename, str)) else ""))
                            raise testcase_exceptions.AbandonTestcase("PARENT PROCESS RAISED OSEXCEPTION %s %s" % \
                                (e.strerror, ("for" + e.filename) if (hasattr(e,"filename") and isinstance(e.filename, str)) else ""))
                                

            # - - - - - - - - - - - - - - - - - - - - -
            #    Record exit code (or signal if program failed
            # - - - - - - - - - - - - - - - - - - - - -

            # Note: if rc is positive, that's an exit(rc) code
            # from called program. If negative, then 
            # process with killed with signal -rc.
            # Common negative rcs include:
            #      -6  SIGABORT
            #     -11  SIGSEGV
            # callStatustoJSON turns these into JSON that 
            # we put into the exitcodefile
            with open(exitcodefilename, "w") as exitcodefile:
                if not foundExecutable:
                    exitcodefile.write("{\"executablenotfound\" : \"%s\"}\n" % progname)
                elif strerror:
                    exitcodefile.write("{\"executablelauncherror\" : \"%s\"}\n" % strerror)
                else:
                    exitcodefile.write(callStatustoJSON(rc) + "\n")

            # - - - - - - - - - - - - - - - - - - - - -
            #    Record valgrind results, if any
            # - - - - - - - - - - - - - - - - - - - - -
            #
            # If valgrind was run valgrindSummaryJSON should find the
            # log and return the JSON summary. If valgrind was not run
            # the None is returned and we don't write a valgrind summary file
            #
            valgrindJSON = None         # in case no log file because valgrind not used
            try:
                with open(valgrindlogfilename, "r") as valgrindlogfile:
                    valgrindJSON = valgrind.valgrindSummaryJSON(valgrindlogfile)
            except IOError as e:
                pass
            except valgrind.ValgrindLogError as e:
                pass
            if valgrindJSON:
                with open(valgrindJSONfilename, "w") as valgrindJSONfile:
                    valgrindJSONfile.write(valgrindJSON)            
                    valgrindJSONfile.write("\n")            

            # - - - - - - - - - - - - - - - - - - - - -
            #    If the testcase descrition asks for canonical
            #    forms of any output files, and if execution
            #    was successful, create them
            # 
            #    If exceptions show there is no 
            # - - - - - - - - - - - - - - - - - - - - -
                    
            if rc == 0 and self.hasProperty("canonical"):
                self.canonicalize(self.canonical)
         
               

            # - - - - - - - - - - - - - - - - - - - - -
            #    Return the exitcode (positive) or signal number (negative)
            #    that resulted from running the program
            # - - - - - - - - - - - - - - - - - - - - -
            return rc

            # - - - - - - - - - - - - - - - - - - - - -
            #    NEEDSWORK: disposition of exceptions needs to be thought through
            #               much more carefully
            # - - - - - - - - - - - - - - - - - - - - -

                      
        # - - - - - - - - - - - - - - - - - - - - -
        #    AbandonTestcase is raised if this run is unsuccessful
        #    but if we think it's worth going on to another testcase.
        #    We record the failure in the exitcodefile.
        # - - - - - - - - - - - - - - - - - - - - -
        
        except testcase_exceptions.AbandonTestcase as e:
            with open(exitcodefilename, "w") as exitcodefile:
                exitcodefile.write("{\"abandontestcaseexception\" : \"%s\"}\n" % str(e))
            raise
                            
        except Exception as e:
            print("Unexpected exception running test program: {}".format(e), file=sys.stderr)
            raise 
        
        


#**********************************************************************
#              TEST CODE FOR THESE CLASSES
#**********************************************************************
     
if __name__ == "__main__":
    assert False, "NEEDSWORK: self-testing for testcase.py is broken due to changes in directory structures and new rules for passing environemnts to runtests"
    env = {
        "testdir" : ".",
        "studentdir" : ".",
        "studentuid" : "dummystudent",
        "testeruid" : pwd.getpwuid(os.getuid()).pw_name,
        "testsetname" : "DummyTest"
       }
    env["studentdir"] = "dummystudent.3"       # local name of dir e.g. studentname.3
    env["studentabsdir"] = os.path.abspath(env["studentdir"])  # full path
    env["resultscontainerdir"] = "."


    print("Running testcase.py test code")

    testTest = Test({"name" : "test1andtest2",
                     "description" : "Duplines on sample files test1 and test2",
                     "programdir" : ".",
                     "program" : "duplines",
                     "arglist" : ["test1.data", "test2.data#{name}"],
                     "resultscontainerdir" : "."
                     });
    testTest.validateProperties()


    testTest2 = Test({"name" : "Anothertest",
                     "description" : "Yet Another Test",
                     "programdir" : ".",
                     "program" : "duplines",
                     "arglist" : ["test1.data", "test2.data", "test3.data"],
                     "resultscontainerdir" : "."
                     });
    testTest2.validateProperties()




