#!/bin/env python3
#
#                  backtick.py
#
#        Noah M. is missing the `` feature of Ruby, so this
#        offers an approximation in Python
#
#        run(command, stdin=None, shell=False)
#        Command can be a string or sequence with command name and args
#
#        Return is a tuple of length 2:
#
#           (ReturnCode, captured_stdout)
#
#        If attempting to execute the command throws an error, then
#        retcode == backtick.ExecutionFailure
#
#        stderr is intercepted unless you call with stderr=None
#        exception output is always appended to the output return value
#
import subprocess

ExecutionFailure = "Failure to execute command"

def run(cmd, stdin=None, stderr=subprocess.STDOUT, shell=False):
    output = ''
    try:
        output = subprocess.check_output(cmd, stdin=stdin, stderr=stderr, shell=shell).decode("utf-8")
#        print("OUTPUT: " + output)
    except subprocess.CalledProcessError as e:
#       print("CALLED PROCESS ERROR: " + repr(e) + e.output.decode("utf-8")
        retcode = e.returncode
        # If we are redirecting error output then we should also return this
        # error output. If 
        output += e.output.decode("utf-8")
    except Exception as e:
#        print(repr(e))
        retcode = ExecutionFailure
        output += str(e)
    else:
        retcode = 0
    return (retcode, output)
