/*
 * CS 15 HW1 test15
 * ElementAt()
 * On index out of range
 * 
 * Ethan  Harvey
 * 09/24/2021
 */
#include "CharArrayList.h"
#include <iostream>

int main() {
    CharArrayList list1('A');
    /* Should print - "index 1 not in range [0..1)" */
    try
    {
        std::cout << list1.elementAt(1) << std::endl;
        // The below should not print
        std::cout << "This should not print! Student did not correctly throw "
                     "a range_error." 
                  << std::endl;
    }
    catch(const std::range_error& e)
    {
        std::cerr << e.what() << '\n';
    }
    
    

    char comp[3] = {'X', 'Y', 'Z'};
    CharArrayList list2(comp, 3);
    /* Should print - "index 3 not in range [0..3)" */

    try
    {
        std::cout << list2.elementAt(3) << std::endl;
    }
    catch(const std::range_error& e)
    {
        std::cerr << e.what() << '\n';
        return 0;
    }
    
    // The below should not print
    std::cout << "This should not print! Student did not correctly throw "
                 "a range_error." 
              << std::endl;
    return 0;
}