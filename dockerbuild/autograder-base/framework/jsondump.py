#!/bin/env python
#
#                          jsondump.py
#
#         Reads the json output of the duplines COMP 40 assignment
#         and summarizes it on stdout. Note that this version
#         sorts the file array by filename

import asciijson, sys


def get_filekey(filepair):
    return filepair["filename"] + str(filepair["linenum"])

if (len(sys.argv) > 2):
    print "Usage: %s [<filename>] | [-]  ('-' or no argument reads STDIN)" % (sys.argv[0])
    sys.exit(1)

if (len(sys.argv) == 1 or sys.argv[1] == "-"):
    filename = "STDIN"
    f = sys.stdin
else:
    try:
        filename = sys.argv[1]
        f = open(sys.argv[1])
    except IOError:
        print "%s: Could not open or read file %s" % (sys.argv[0], filename)
        sys.exit(1)

jsondata = f.read()
f.close()

try:
    data = asciijson.loads(jsondata)
except ValueError:
    print "%s: Could not parse %s as JSON" % (sys.argv[0], filename)
    sys.exit(1)


for line, filearray in data.items():
    print '"' + line +  '" occurs in:'
    sortedFileArray = sorted(filearray, key=get_filekey)
    for filepair in sortedFileArray:
        print "File: " + filepair["filename"] + " Line: " + str(filepair["linenum"])
    print             # newline

