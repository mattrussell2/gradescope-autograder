#!/bin/env python
#
#                          runtest.py
#
#        Experimental program to invoke a test routine and capture the output
#


import asciijson, sys, subprocess

test = {
    "name" : "test1andtest2",
    "programdir" : ".",
    "program" : "duplines",

    "args" : ["test1.data", "test2.data"]

}


def doATest(testconf):
    try:
        progname = testconf["programdir"] + '/' + testconf["program"]
        args = [ progname ]
        args.extend(testconf["args"])
        print "Hello"
        stoutname = testconf["name"] + '.stdout'
        sterrname = testconf["name"] + '.stderr'
        print ', '.join(map(str, args))
        rc = 0
        with open(stoutname, "w") as stoutfile:
            with open(sterrname, "w") as sterrfile:
                rc = subprocess.call(args, stdout=stoutfile, stderr=sterrfile);
        return rc
    except Exception as e:
        print 'Exception running test program: %s' % e
        sys.exit(1);

print "Starting test"
rc = doATest(test)

print 'test returned: %d' % rc

