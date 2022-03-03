#!/usr/sup/bin/python
#
#                  hook.py
#
#        Author: Noah Mendelsohn
#      
#    Provides dynamic loading facilities for modules that users can override
#    or "hook"
#     

#
#                      load
#
#
#     The object with name modname.objectName is loaded. Modname may use
#     package qualification.
#
#     If not already there, path is temporarily added to sys.path. Path may be
#     None in which case the existing path is used.
#
#     Details of search:
#
#       1) Attempt is made to load modname with supplied path put at
#          head of path list, which means it will be found if in the
#          supplied path. If that works, that module is used.
#       2) If that fails, the module name has builtin. prepended, which
#          means that if there is a builtin package in the search path
#          for the test framework code, that will resolve.
#       3) Iff and the above resolve, then the supplied objectName is located
#          in the module. The module
#
#     Comments clarified by Noah 12/30/2020. He believes these are now accurate.
#

import importlib, sys, os

DEFAULTMODULEPREFIX = "builtin"

DEBUGOUT = False

def DEBUG_PRINT(s):
    if DEBUGOUT:
        print(s, file=sys.stderr)

def load(path, modname, objectName, fallbackModulePrefix=DEFAULTMODULEPREFIX):
    #
    #  If supplied path is not already in sys.path, add it temporarily
    #
    DEBUG_PRINT("In hook: path={}, modname={}, objectName=(), fallbackPrefix={}".
                format(path, modname, objectName, fallbackModulePrefix))
    hadPath = path == None or path in sys.path
    if not hadPath:
        sys.path.insert(0, path)
        
    mod = None
    try:
        mod = importlib.import_module(modname)
    except ImportError as e:
        if fallbackModulePrefix:
            fallbackModname = '.'.join( (fallbackModulePrefix,modname ) )
            try:
                mod = importlib.import_module(fallbackModname)
            except ImportError as e:
                DEBUG_PRINT("In Hook importing fallback module {}: IMPORTERROR = {}".format(fallbackModname, str(e)))
                pass
        else:
            pass  # Not trying default location because defaultModulePrefix=None (1/4/2021)
    
    #
    #    Done with sys.path, take out temporary entry
    #
    if not hadPath:
        sys.path.remove(path)

    #
    #    If we found the module, return the requested object, leaving
    #    module loaded as a side-effect
    #
    if mod:
        if hasattr(mod, objectName):
            obj =  getattr(mod, objectName)
            return obj
        else:
            DEBUG_PRINT("...load({}, {}, {}) FAILED".format(path, modname, objectName))
            return None
    else:
#       DEBUG_PRINT("Did not successfully import module")
        return None

        
        
#
#   This is a more vanilla version that does not do defaulting
#   Exceptions are left to percolate out. 
#
#   This is useful with path="." to make sure modules in current dir are found
#
def load_no_default(path, modname, objectName):
    DEBUG_PRINT("hook:load_no_default: Path %s abspath %s" % (path, os.path.abspath(path)))
    #
    #  If supplied path is not already in sys.path, add it temporarily
    #
    hadPath = path == None or path in sys.path
    if not hadPath:
        sys.path.insert(0, path)
        
    mod = None
    try:
        mod = importlib.import_module(modname)
    finally:
        #
        #    Done with sys.path, take out temporary entry
        #
        if not hadPath:
            sys.path.remove(path)

    #
    #    If we found the module, return the requested object, leaving
    #    module loaded as a side-effect
    #
    if hasattr(mod, objectName):
        obj =  getattr(mod, objectName)
    else:
        raise AttributeError("Module {} loaded but could not find object {}".format(modname, objectName))

    #
    #  Return the module and the object (which will very often be a method)
    #
    return (mod, obj)
