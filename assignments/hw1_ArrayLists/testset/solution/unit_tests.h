/*
 * unit_tests.h
 *
 * CS 15 homework 1
 * by Tyler Calabrese, January 2021
 *
 * Uses Matt Russell's unit_test framework to test the CharArrayList class.
 *
 * Instructions for using testing framework can be found at in CS 15's lab
 * 1 -- both in the spec and in the provided ArrayList_tests.h and Makefile.
 * More in-depth information for those who are curious as to how it works can
 * be found at http://www.github.com/mattrussell2/unit_test.
 */

#include "CharArrayList.h"
#include <cassert>

/********************************************************************\
*                       CHAR ARRAY LIST TESTS                        *
\********************************************************************/

/* To give an example of thorough testing, we are providing
 * the unit tests below which test the insertAt function. Notice: we have
 * tried to consider all of the different cases insertAt may be 
 * called in, and we test insertAt in conjunction with other functions!
 *
 * You should emulate this approach for all functions you define.
 */




/* REMOVE THIS COMMENT (including the end-of-comment at the bottom of the file)
 * once you have implemented your insertAt function and are ready to test it.

// Tests correct insertion into an empty AL.
// Afterwards, size should be 1 and element at index 0
// should be the element we inserted.
void insertAt_empty_correct()
{
    CharArrayList test_list;
    test_list.insertAt('a', 0);
    assert(test_list.size() == 1);
    assert(test_list.elementAt(0) == 'a');
}

// Tests incorrect insertion into an empty AL.
// Attempts to call insertAt for index larger than 0.
// This should result in an std::range_error being raised.
void insertAt_empty_incorrect()
{
    // var to track whether range_error is thrown
    bool range_error_thrown = false;

    // var to track any error messages raised
    std::string error_message = "";

    CharArrayList test_list;
    try {
        // insertAt for out-of-range index
        test_list.insertAt('a', 42);
    }
    catch (const std::range_error &e) {
        // if insertAt is correctly implemented, a range_error will be thrown,
        // and we will end up here
        range_error_thrown = true;
        error_message = e.what();
    }

    // out here, we make our assertions
    assert(range_error_thrown);
    assert(error_message == "index (42) not in range [0..0]");
}

// Tests correct insertAt for front of 1-element list.
void insertAt_front_singleton_list()
{
    // initialize 1-element list
    CharArrayList test_list('a');

    // insert at front
    test_list.insertAt('b', 0);

    assert(test_list.size() == 2);
    assert(test_list.elementAt(0) == 'b');
    assert(test_list.elementAt(1) == 'a');
}

// Tests correct insertAt for back of 1-element list.
void insertAt_back_singleton_list()
{
    // initialize 1-element list
    CharArrayList test_list('a');
    
    // insert at back
    test_list.insertAt('b', 1);

    assert(test_list.size() == 2);
    assert(test_list.elementAt(0) == 'a');
    assert(test_list.elementAt(1) == 'b');
}

// Tests calling insertAt for a large number of elements.
// Not only does this test insertAt, it also checks that
// array expansion works correctly.
void insertAt_many_elements()
{
    CharArrayList test_list;

    // insert 1000 elements
    for (int i = 0; i < 1000; i++) {
        // always insert at the back of the list
        test_list.insertAt('a', i); 
    }

    assert(test_list.size() == 1000);

    for (int i = 0; i < 1000; i++) {
        assert(test_list.elementAt(i) == 'a');
    }
}

// Tests insertion into front, back, and middle of a larger list.
void insertAt_front_back_middle()
{

    char test_arr[8] = { 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h' };    
    CharArrayList test_list(test_arr, 8);

    // insertAt middle
    test_list.insertAt('z', 3);

    assert(test_list.size() == 9);
    assert(test_list.elementAt(3) == 'z');
    assert(test_list.toString() == "[CharArrayList of size 9 <<abczdefgh>>]");

    // insertAt front
    test_list.insertAt('y', 0);

    assert(test_list.size() == 10);
    assert(test_list.elementAt(0) == 'y');
    assert(test_list.toString() == "[CharArrayList of size 10 <<yabczdefgh>>]");

    // insertAt back
    test_list.insertAt('x', 10);

    assert(test_list.size() == 11);
    assert(test_list.elementAt(10) == 'x');
    assert(test_list.toString() == "[CharArrayList of size 11 <<yabczdefghx>>]");
}

// Tests out-of-range insertion for a non-empty list.
void insertAt_nonempty_incorrect()
{
    char test_arr[8] = { 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h' };    
    CharArrayList test_list(test_arr, 8);

    // var to track whether range_error is thrown
    bool range_error_thrown = false;

    // var to track any error messages raised
    std::string error_message = "";

    try {
        test_list.insertAt('a', 42);
    }
    catch (const std::range_error &e) {
        range_error_thrown = true;
        error_message = e.what();
    }

    assert(range_error_thrown);
    assert(error_message == "index (42) not in range [0..8]");
}


* END OF COMMENT. REMOVE ONCE YOU HAVE IMPLEMENTED insertAt.
*/

