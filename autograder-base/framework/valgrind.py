#!/usr/sup/bin/python
#
#                  valgrind.py
#
#        Author: Noah Mendelsohn
#      
#   
#      

import os, sys, re, errno 

# True if this log contains valgrind resultshas
hasValgrindRE = re.compile(r"==[0-9]*== Memcheck, a memory error detector") 


# Data Extractors
AllBlocksFreedRE = re.compile(r"==[0-9]*== All heap blocks were freed -- no leaks are possible")
ErrorRE = re.compile(r"==[0-9]*== ERROR SUMMARY: (\d*) errors from (\d*) contexts") 
LostRE = re.compile(r"==[0-9]*==    definitely lost: (\d{1,3}(?:,\d{3})*) bytes in (\d{1,3}(?:,\d{3})*) blocks")

InUseRE = re.compile(r"==[0-9]*==     in use at exit: (\d{1,3}(?:,\d{3})*) bytes in (\d{1,3}(?:,\d{3})*) blocks") 

ReachableRE = re.compile(r"==[0-9]*==    still reachable: (\d{1,3}(?:,\d{3})*) bytes in (\d{1,3}(?:,\d{3})*) blocks")

class ValgrindLogError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
         return self.msg


#************************************************************************
#                          FUNCTIONS
#************************************************************************


#-------------------------------------------------------------
#                      commaSeptoNumber
#
#     Take a string of the form 12,345,678 and return the
#     corresponding integer 12345678
#-------------------------------------------------------------

def commaSeptoNumber(s):
    return int(s.replace(",",""))
    
#-------------------------------------------------------------
#                      hasValgrind
#-------------------------------------------------------------

def hasValgrind(s):
    return hasValgrindRE.search(s)
    
#-------------------------------------------------------------
#                      valgrindErrors
#-------------------------------------------------------------

def valgrindErrors(s):
    errorMatch = ErrorRE.search(s)
    if not errorMatch:
        raise ValgrindLogError("valgrind.py error log appears to include valgrind run but has no ERROR SUMMARY")
    return (errorMatch.group(1), errorMatch.group(2))
    
#-------------------------------------------------------------
#                      valgrindLostInUse
#-------------------------------------------------------------

def valgrindLostInUse(s):
    #
    # If valgrind log shows all blocks free, then nothing is lost!
    #
    everythingFine = AllBlocksFreedRE.search(s)
    if everythingFine:
        return(0, 0, 0, 0, 0, 0)       

    #
    # Something was lost, find out exactly what
    #
    lostMatch = LostRE.search(s)
    if not lostMatch:
        raise ValgrindLogError("Error: valgrind.py error log appears to include valgrind run but has no definitely lost")
    reachableMatch = ReachableRE.search(s)
    if not reachableMatch:
        raise ValgrindLogError("Error: valgrind.py error log appears to include valgrind run but has no still reachable")
    inUseMatch = InUseRE.search(s)
    if not inUseMatch:
        raise ValgrindLogError("Error: valgrind.py error log appears to include valgrind run but has no still in use")
    return tuple(map(commaSeptoNumber,[lostMatch.group(1), lostMatch.group(2), reachableMatch.group(1), reachableMatch.group(2), inUseMatch.group(1), inUseMatch.group(2)]))
    
    
#-------------------------------------------------------------
#                      valgrindSummaryJSON
#
#      Argument
#
#      File descriptor of file open for reading, containing
#      an stderr log from a valgrind run. 
#
#      Return Value:
#
#      If the error log appears to contain valgrind results, then
#      a JSON summary of those results, otherwise None.
#
#-------------------------------------------------------------

def valgrindSummaryJSON(fd):
    log = fd.read()
    if not hasValgrind(log):
        return None
    #
    #  Valgrind was used, extract error counts
    #
    errors, groups = valgrindErrors(log)  #these are strings for now NEEDSWORK

    #the following are integers
    lostBytes, lostBlocks, reachableBytes, reachableBlocks, heapInUseBytes, heapInUseBlocks = valgrindLostInUse(log)
    
    retval =  "{\"Errors\" : %s, \"HeapInUseBytes\" : %d, \"DefinitelyLostBytes\" : %d , \"StillReachableBytes\" : %d }" % (errors, heapInUseBytes, lostBytes, reachableBytes)
    return retval

    
    
#**********************************************************************
#              TEST CODE FOR THESE CLASSES
#**********************************************************************
     
ValgrindTestFileName = "valgrind_test_log.txt" 
NotValgrindTestFileName = "not_valgrind_test_log.txt" 
if __name__ == "__main__":
    #
    # Test case where valgrind was run
    #
    with open(ValgrindTestFileName, "r") as logfile:
        summary = valgrindSummaryJSON(logfile)
    if summary == None:
        print("No JSON found in test file {}".format(ValgrindTestFileName))
    else:
        print("{}".format(summary))

    #
    # Test case where valgrind was not run
    #
    with open(NotValgrindTestFileName, "r") as logfile:
        summary = valgrindSummaryJSON(logfile)
    if summary == None:
        print("No JSON found in test file {}".format(NotValgrindTestFileName))
    else:
        print("BAD NEWS, JSON WAS RETURNED FOR NON-VALGRIND FILE {}".format(NotValgrindTestFileName))
        print("{}".format(summary))



