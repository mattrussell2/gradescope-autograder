#!/bin/env python
#
#                  utilities.py
#
#        Author: Noah Mendelsohn
#      
#    Miscellaneous shared utility routines.
#        

import os, errno

#
#  make a directory but be silent if it already exists
#  NEEDSWORK: permissions on the dir?
#
def mkdir(d):
    try:
        os.makedirs(d)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
    return d
    
#
#   forceRemoveFile
#
#      Remove a file, proceeding silently if it did not exist
def forceRemoveFile(filename):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise                   # re-raise exception if a different error occured
