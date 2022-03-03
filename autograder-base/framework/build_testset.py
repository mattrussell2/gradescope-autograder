#!/bin/env python3
#
#                       build_testset.py
#                  Author: Noah Mendelsohn
#
#        Main inputs:
#        ------------
#
#            A testset specification package file, which is a JSON file specifying
#            the following:
#
#            1) testset_template: a JSON file with all the fixed boilerplate
#               that forms the outermost json for the testset. This will
#               be at least all the boilerplate such as description and a possibly
#               empty "tests" : [] list. If the tests list is non-empty, then
#               those tests will appear in the generated testset ahead of the
#               ones from step 2. For example, an initial step to compile
#               a program might be included in this outer template.
#
#            2) One or more json or csv files and/or :
#                  *  If JSON,  each must be a list of 
#                     dictionaries in the form of the entries 
#                     that comprise the "tests" list in a testset. 
#                  *  If CSV, then the headers must be keys such as "name"
#                     "datadir" etc that comprise a test. The "name" key 
#                     is required. Each row will be mapped to a Python dictionary
#                     that ultimately will be written as json in the final testset
#                     file.
#                  *  If Python, then the module will be loaded and the 
#                     indicated method will be called. It is 
#                     to return an iterable list of dictionary-like objects,
#                     similar in form to the JSON option above
#
#                Because order is important, the csv and json files are
#                supplied in single ordered list. Thus, the filename extensions
#                must be .csv and .json respectively so we will know how to
#                parse them.
#
#         Construction of the output testset:
#         -----------------------------------
#
#         The output testset is the json for the testset_template, augmented
#         as follows:
#
#         The fields for each named test are the combined values specified in all
#         the per-test json and csv files, merged in order as encountered in the
#         csv and json files.
#               

import argparse, os, sys, json, csv, os.path
import hook

from collections import OrderedDict

DEBUGOUT = False

TESTS_KEY = "tests"      # the key in the testsets for the enumerated tests
TESTSET_TEMPLATE_KEY = "testset_template"
TEST_TEMPLATE_KEY = "test_template"
TESTNAME_KEY = "name"      # the key in each enumerated test that names the test
TESTGROUPS_KEY = "testgroups" 
PACKAGE_LABEL_KEY = "package"

#
#  Keys in the package file for data sources for JSON and CSVspecifications
#
SPECIFICATION_FILENAME_KEY = "specification_filename"
SPECIFICATION_FILE_FORMAT_KEY = "specification_file_format"

#
#  Keys in the package file for Python data sources
#
PYTHON_MODULE_NAME_KEY = "python_module"
PYTHON_METHOD_NAME_KEY = "python_method"



def debug_print(s):
    if DEBUGOUT:
        print(s,file=sys.stderr)

#---------------------------------------------------------------
#                     counters
#---------------------------------------------------------------

number_of_tests_created = 0
number_of_tests_updated = 0

#---------------------------------------------------------------
#                     parseargs
#
#    Use Python standard argument parser to parse arguments and provide help
#---------------------------------------------------------------

def parseargs():
    parser = argparse.ArgumentParser()
#    parser.add_argument("-format", nargs=1, help="Build a testset from a template", \
#                            choices=[JSONFORMATKEY, CSVFORMATKEY, COMP40FORMATKEY], \
#                            default=[COMP40FORMATKEY])
    parser.add_argument("--output", nargs=1, default=sys.stdout, required=False, help="Name of output testset file (default is stdout)'")
#    parser.add_argument('--testset_template', help="Overall template for the testset (json)", nargs=1, required=True)
#    parser.add_argument('--test_template', help="Template for individual test (json)", nargs=1, required=True)
    parser.add_argument('specification_package', help="json file specifying individual templates and test specifications to be assembled")
    return parser.parse_args()

#---------------------------------------------------------------
#                           update_tests
#
#       Takes in a list (assumed to be a list of tests), 
#       and a list of orderderddicts that (assumed to be new fields for
#       whichever test the TEST_NAME field identifies, including
#       the TEST_NAME field.
#
#       Note: use of this relies on the tests arg being passed by ref
#      
#---------------------------------------------------------------

def update_tests(tests, new_tests_data, new_test_template):
    for new_test_data in new_tests_data:
        debug_print("\n\nCalling update_test on: " + repr(new_test_data))
        update_test(tests, new_test_data, new_test_template)

def update_test(tests, new_test_data, new_test_template):
    global number_of_tests_created, number_of_tests_updated
    assert TESTNAME_KEY in new_test_data, "New test data {} has no {} key (required)".format(repr(new_test_data), TESTNAME_KEY)

    testname = new_test_data[TESTNAME_KEY]

    #
    # Find the index 
    match = None
    for i, test in enumerate(tests):
        if test[TESTNAME_KEY] == testname:
            match = i
            break
    
    #
    # If we matched, then we already have data for this test, augment it
    #
    if match:
        debug_print("Matched on testname {}, extending.".format(testname))
       # 
        # We want to retain the original copy of the TESTNAME (name) field
        # because it tends to come early. Note, this destructively changes new_test_data
        #
        del new_test_data[TESTNAME_KEY]
        # The following should merge the two OrderedDicts in order
        # replacing what was there
        tests[i] = OrderedDict(list(tests[i].items()) + 
                                           list(new_test_data.items()))
        number_of_tests_updated += 1
    #
    #  The testname is not in the template, the new_test_data becomes the
    #  whole test
    #
    else:
        debug_print("Creating new test named {}.".format(testname))        
        tests.append(OrderedDict(list(new_test_template.items()) + 
                                           list(new_test_data.items())))
        number_of_tests_created += 1

    
#---------------------------------------------------------------
#                           get_JSON_from_file
#---------------------------------------------------------------

def get_JSON_from_file(fname):
    try:
        with open(fname, "r", encoding="ascii") as template_f:
            return json.load(template_f, object_pairs_hook=OrderedDict)
    except Exception as e:
        print("Exception opening or parsing JSON file: {}".format(fname), file=sys.stderr)
        print(str(e), file=sys.stderr)
        raise e

#---------------------------------------------------------------
#                           do_JSON_file
#---------------------------------------------------------------

def do_JSON_file(fname, results, new_test_template):
    data = get_JSON_from_file(fname)
    # This updates results[TEST+KEY] in place. Note that typically this is
    # updating results["tests"]
    update_tests(results[TESTS_KEY], data, new_test_template)



#---------------------------------------------------------------
#                           get_CSV_from_file
#---------------------------------------------------------------

def get_CSV_from_file(fname):
    with open(fname, newline='', encoding='ascii') as f:
        reader = csv.DictReader(f)
        return list(reader)


#---------------------------------------------------------------
#                           do_CSV_file
#---------------------------------------------------------------

def do_CSV_file(fname, results, new_test_template):
    data = get_CSV_from_file(fname)
    
    # This updates results[TEST+KEY] in place. Note that typically this is
    # updating results["tests"]
    update_tests(results[TESTS_KEY], data, new_test_template)


#---------------------------------------------------------------
#                           do_python_specification
#
#    Load the indicated python module and run the supplied method
#    
#---------------------------------------------------------------

def do_python_specification(python_module_name, method_name, new_test_template):
    #
    #  Load the Python module and find the method object within it
    #
    try:
        specification_module, specification_method = hook.load_no_default(".", python_module_name, method_name)
#        print(repr(specification_module))
    except ImportError as e:
        print("Could not import Python specification module: {}".format(python_module_name), file=sys.stderr)
        print(repr(e), file=sys.stderr)
        sys.exit(4)
    except AttributeError as e:
        debug_print("Could not find method {}in Python specification module: {}".format(method_name, python_module_name), file=sys.stderr)
        print(repr(e), file=sys.stderr)
        sys.exit(4)

    #
    #   Call the supplied method and update the results
    #
    update_tests(results[TESTS_KEY], specification_method() , new_test_template)



#---------------------------------------------------------------
#                           main
#
#    Use Python standard argument parser to parse arguments and provide help
#---------------------------------------------------------------

args = parseargs()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
#           Handle the package file preamble
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

#
#   Get the package specification for the whole testset
#
specification_package_fname = args.specification_package

package = get_JSON_from_file(specification_package_fname)

assert package.get(PACKAGE_LABEL_KEY,'false').lower() == 'true', "Testset specification packages must have a key 'package' with value 'True'\nThis is done to avoid accidentally using a testset_template as a package"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
#           Get the overall templage
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

#
# Get the overall template as an  OrderedDict
#
testset_template_fname = package[TESTSET_TEMPLATE_KEY]
results = get_JSON_from_file(testset_template_fname)
    
# debug_print("OUTER TESTSET TEMPLATE\n----------------------\n\n" + repr(results) + 
#             "---------------------------------------------------\n")

assert TESTS_KEY in results, "Template {} must contain a {} key".format(template_fname,
                                                                                TESTS_KEY)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
#         If there is a testgroups specification
#         then process each testgroup  
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

testgroups = package.get(TESTGROUPS_KEY, [])

for n, testgroup in enumerate(testgroups):

    #
    # Get the individualtemplate as an  OrderedDict
    #
    test_template_fname = testgroup.get(TEST_TEMPLATE_KEY, None)
    assert test_template_fname, "Test group {} must have a {}".format(n, TEST_TEMPLATE_KEY)
    test_template = get_JSON_from_file(test_template_fname)
    
    # debug_print("INDIVIDUAL TEST TEMPLATE\n----------------------\n\n" + repr(results) + 
    #             "---------------------------------------------------\n")


    # 
    # Load the specification file for this testgroup and process it
    #
    
    python_module_name = testgroup.get(PYTHON_MODULE_NAME_KEY, None)
    
    if python_module_name:
        #
        # This is a loadable python module
        #
        python_method_name = testgroup.get(PYTHON_METHOD_NAME_KEY, None)
        assert python_method_name, "No {} specified for Python module {}".format(
            PYTHON_METHOD_NAME_KEY, python_module_name)
        do_python_specification(python_module_name, python_method_name, test_template)

        
    else:
        #
        #  JSON or CSV FILE
        specification_filename = testgroup[SPECIFICATION_FILENAME_KEY]
        specification_file_format = testgroup[SPECIFICATION_FILE_FORMAT_KEY]
        
        filenamebase, file_extension = os.path.splitext(specification_filename)
        file_extension = file_extension[1:]    # splitext preserves dot, e.g. .json
    
        #
        # CSV Files
        #
        if file_extension.lower() == 'csv':
            do_CSV_file(specification_filename, results, test_template)
        #
        # JSON Files
        #
        else:
            assert file_extension.lower() == "json", "Test file {} is neither CSV nor JSON"\
                                 .format(specification_filename)
            do_JSON_file(specification_filename, results, test_template)
    

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
#              write the output
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

outfile = sys.stdout if args.output==sys.stdout else open(args.output[0], "w", newline="")

json.dump(results, outfile, ensure_ascii=True, indent=4)

print("Number of tests created: {:d}  Number of tests updated: {:d}".\
      format(number_of_tests_created, number_of_tests_updated), file=sys.stderr)

outfile.close()

