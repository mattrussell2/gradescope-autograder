#!/bin/env python
#
#                  backtick.py
#
#        Noah M. is missing the `` feature of Ruby, so this
#        offers an approximation in Python
#
#        run(command, stdin=None)
#        Command can be a string or sequence with command name and args
#
#        Return is a tuple of length 2:
#
#           (ReturnCode, captured_stdout)
#
#        If attempting to execute the command throws an error, then
#        retcode == backtick.ExecutionFailure
#
#        stderr is not intercepted
#
import subprocess

ExecutionFailure = "Failure to execute command"

def run(cmd, stdin=None):
    output = ''
    try:
        output = subprocess.check_output(cmd, stdin=stdin)
    except subprocess.CalledProcessError as e:
        retcode = e.returncode
    except Exception as e:
        retcode = ExecutionFailure
    else:
        retcode = 0
    return (retcode, output)
