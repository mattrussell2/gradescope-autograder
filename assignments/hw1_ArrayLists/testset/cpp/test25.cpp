/**
 * CS15 HW1 TEST 25
 * 
 * insertAt() out of range [size + 1]
 * 
 * mchamp03
 * 9/25/2021
 */

#include <iostream>
#include "CharArrayList.h"


int main() {

    char passe[]  = {'p', 'a', 's', 's', 'e'};

    CharArrayList passed(passe, 5);
    /* should print "index (6) not in range [0..5]" */
    try
    {
        passed.insertAt('d', 6);
    }
    catch(const std::range_error& e)
    {
        std::cerr << e.what() << '\n';
        return 0;
    }
    
    
    // The below should not print
    std::cout << "This should not print! Student did not correctly throw a range_error." 
              << std::endl;
    return 0;
}