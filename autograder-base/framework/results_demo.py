#!/bin/env python3
#
#                  results_demo.py
#
#        Author: Noah Mendelsohn
#
#   A simple demo to illustrate use of Results3 and subsets
#     


import argparse, os, sys, os.path

from results import Results3        # Class that holds all the test results summary data




#*****************************************************************************
#                     parseargs
#
#    Use Python standard argument parser to parse arguments and provide help
#
#*****************************************************************************


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", 
                        nargs=1, required=False, 
                        help="Report on this category",
                        default=[None])

    parser.add_argument('summaryFilenames', help="input testset summary files",
                        nargs="+")
    return parser.parse_args()
 

#*****************************************************************************
#                          demo
#
#   Called to do the demonstration after the Results3 object (resultsData)
#   has been created from the JSON files.
#
#   This demo first prints all results by student, then prints 
#   failed results by student, demonstrating subset intersection.
#
#   If a category is supplied, then do by student in the category.
#
#   Notes: 
#
#       * ResultsSubset objects are fundamentally a predicate function
#         (e.g. lambga r: r["success"] == "FAILED") and a corresponding
#         list of indices in the resultsData for objects meeting that
#         predicate.
#
#       * Although it's implicit in their position in the list, each
#         object in the resultsData list is a dict that includes an
#         _INDX key which explicitly gives its index in the Python list
#
#       * s1 & s2 on two ResultsSubset objects yields an ordinary Python
#         set of indices, not a ResultsSubset object (perhaps that's
#         unfortunate, but that's how it works for now)
#
#       * GroupedResultsSubsets (like byStudent) are like dicts with a key
#         (student in this example) for each of which there is a 
#         resultsSubset (e.g. tests for that student)
#
#*****************************************************************************


def demo(resultsData, category):

    print_major_box("DEMONSTRATING BY STUDENT")
    for studentName, subset in resultsData.byStudent.items():
        printHeader("Student: " + studentName)
        printSubset(subset)
        print()


    print_major_box("DEMONSTRATING INTERSECTION USING FAILED TESTS")

    # all failed tests, regardless of student
    # Note that this is a precomputed subset that's
    # automatically available on all Results3 objects.
    # See the results.py source file for the list
    # of built in subsets like this

    failed_tests_subset = resultsData.failed
    print(failed_tests_subset)
    
    for studentName, subset in resultsData.byStudent.items():
        printHeader(" FAILED TESTS for Student: " + studentName)
        #
        # Compute a Python set (not a ResultsSubset) of the
        # resultsData indices of the failed tests for this
        # students. This relies on the fact that the & operator is
        # supported on ResultsSubsets, yielding an ordinary Python set
        # of indices (you can make the case it should yield another
        # ResultsSubset, but that's not currently how the code works.
        #
        indices_of_failed_for_student = failed_tests_subset & subset
        print("Indices_Of_Failed_For_Student: " + repr(indices_of_failed_for_student))

        for indx in indices_of_failed_for_student:
            print(resultsData[indx])
        print()

    if category:
        print_major_box("DEMONSTRATING INTERSECTION USING SUPPLIED CATEGORY")

        # all failed tests, regardless of student
        # Note that this is a precomputed subset that's
        # automatically available on all Results3 objects.
        # See the results.py source file for the list
        # of built in subsets like this

        category_tests_subset = resultsData.byCategory[category]
        print(category_tests_subset)
    
        for studentName, subset in resultsData.byStudent.items():
            printHeader(f" TESTS IN CATEGORY {category} for Student: {studentName}")
            #
            # Compute a Python set (not a ResultsSubset) of the
            # resultsData indices of the failed tests for this
            # students. This relies on the fact that the & operator is
            # supported on ResultsSubsets, yielding an ordinary Python set
            # of indices (you can make the case it should yield another
            # ResultsSubset, but that's not currently how the code works.
            #
            indices_in_category_for_student = category_tests_subset & subset
            print("Indices_In_Category_For_Student: " + repr(indices_in_category_for_student))

            for indx in indices_in_category_for_student:
                print(resultsData[indx])
            print()
    else:
        print_major_box("--category arg not supplied...NO CATEGORY DEMO")


#*****************************************************************************
#                         Printing Functions
#*****************************************************************************

WIDTH=65
SEP = "=" * 65

def print_major_box(txt):
    print(SEP)
    print(SEP)
    print("    " + txt)
    print(SEP)
    print(SEP)
    
def printHeader(txt):
        print(SEP)
        print(" " * ((WIDTH - len(txt)) // 2) + txt)
        print(SEP)

def print_single_result(r):
    print(f"Result at index: {r['_INDX']}")

    data = (f"{key}: {r[key]}" for key in sorted(r.keys()))

    print(", ".join(data))

def printSubset(subset):
    print(repr(subset))

    print("Results data for above items")

    for r in subset.results():
        print_single_result(r)


if __name__ == "__main__":
    # - - - - - - - - - - - - - - - - - - - - - - - - 
    #    Parse args and make sure all files are readable before starting
    # - - - - - - - - - - - - - - - - - - - - - - - - 

    args = parseargs()
    category = getattr(args,"category",[""])[0]  # defaults to empty string

    for summaryfilename in args.summaryFilenames:
        assert os.path.isfile(summaryfilename) and os.access(summaryfilename, os.R_OK), \
            "File %s does not exists or is not readable" % summaryfilename


        # - - - - - - - - - - - - - - - - - - - - - - - - 
        #   Gather data from input files
        # - - - - - - - - - - - - - - - - - - - - - - - - 

    resultsData = Results3(files=args.summaryFilenames)


    # - - - - - - - - - - - - - - - - - - - - - - - - 
    #       Play with the results3 data
    # - - - - - - - - - - - - - - - - - - - - - - - - 
    
    demo(resultsData, category)
