#!/bin/env python
#
#                  unixsignals.py
#
#        Author: Noah Mendelsohn
#      
#   
#        Classes:
#
#             Test:     A single test that can be run to yield a result
#             SetofTests: Zero or More tests (designed to be subclassed)
#
#        Note that in principle a set of tests can, in principle, be 
#        represented as a concrete list of Test objects, or can be
#        simulated through iteration using generators.


maxSignal = 34
signals = [
  # We start with a dummy entry so signals[nn] will get the right one
  { "name" : "DUMMY", "value" : 0, "description" : "PLACEHOLDER SO SIGNUM == INDEX" },
  { "name" : "SIGHUP", "value" : 1, "description" : "Hangup" },
  { "name" : "SIGINT", "value" : 2, "description" : "Interrupt" },
  { "name" : "SIGQUIT", "value" : 3, "description" : "Quit" },
  { "name" : "SIGILL", "value" : 4, "description" : "Illegal Instruction" },
  { "name" : "SIGTRAP", "value" : 5, "description" : "Trace/Breakpoint Trap" },
  { "name" : "SIGABRT", "value" : 6, "description" : "Abort" },
  { "name" : "SIGEMT", "value" : 7, "description" : "Emulation Trap" },
  { "name" : "SIGFPE", "value" : 8, "description" : "Arithmetic Exception" },
  { "name" : "SIGKILL", "value" : 9, "description" : "Killed" },
  { "name" : "SIGBUS", "value" : 10, "description" : "Bus Error" },
  { "name" : "SIGSEGV", "value" : 11, "description" : "Segmentation Fault" },
  { "name" : "SIGSYS", "value" : 12, "description" : "Bad System Call" },
  { "name" : "SIGPIPE", "value" : 13, "description" : "Broken Pipe" },
  { "name" : "SIGALRM", "value" : 14, "description" : "Alarm Clock" },
  { "name" : "SIGTERM", "value" : 15, "description" : "Terminated" },
  { "name" : "SIGUSR1", "value" : 16, "description" : "User Signal 1" },
  { "name" : "SIGUSR2", "value" : 17, "description" : "User Signal 2" },
  { "name" : "SIGCHLD", "value" : 18, "description" : "Child Status" },
  { "name" : "SIGPWR", "value" : 19, "description" : "Power Fail/Restart" },
  { "name" : "SIGWINCH", "value" : 20, "description" : "Window Size Change" },
  { "name" : "SIGURG", "value" : 21, "description" : "Urgent Socket Condition" },
  { "name" : "SIGPOLL", "value" : 22, "description" : "Socket I/O Possible" },
  { "name" : "SIGSTOP", "value" : 23, "description" : "Stopped (signal)" },
  { "name" : "SIGTSTP", "value" : 24, "description" : "Stopped (user)" },
  { "name" : "SIGCONT", "value" : 25, "description" : "Continued" },
  { "name" : "SIGTTIN", "value" : 26, "description" : "Stopped (tty input)" },
  { "name" : "SIGTTOU", "value" : 27, "description" : "Stopped (tty output)" },
  { "name" : "SIGVTALRM", "value" : 28, "description" : "Virtual Timer Expired" },
  { "name" : "SIGPROF", "value" : 29, "description" : "Profiling Timer Expired" },
  { "name" : "SIGXCPU", "value" : 30, "description" : "CPU time limit exceeded" },
  { "name" : "SIGXFSZ", "value" : 31, "description" : "File size limit exceeded" },
  { "name" : "SIGWAITING", "value" : 32, "description" : "All LWPs blocked" },
  { "name" : "SIGLWP", "value" : 33, "description" : "Virtual Interprocessor Interrupt for Threads Library" },
  { "name" : "SIGAIO", "value" : 34, "description" : "Asynchronous I/O" }
]



def badSignal(s):
    return { "name" : "SIGUNKNOWN", 
             "value" : s, 
             "description" : "SIGNAL VALUE OUT OF RANGE" }
    
def lookupSignal(s):
    if 1 <= s <= maxSignal:
        return signals[s]
    else:
        return badSignal(s)


def toJSON(s):
    sig = lookupSignal(s)
    return "{ \"signal_name\" : \"%s\", \"signal_value\" : %d, \"signal_description\" : \"%s\" }" % \
        (sig["name"], sig["value"], sig["description"])

#
#  Make cross reference
#

signalsByName = {}

for signal in signals:
    signalsByName[signal["name"]] = signal


