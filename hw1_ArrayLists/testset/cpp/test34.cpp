/**
 * CS15 HW1 TEST 34
 * 
 * replaceAt - out of range - size() + 1
 * 
 * mchamp03
 * 9/25/2021
 */

#include <iostream>
#include "CharArrayList.h"


int main() {

    char passed[]  = {'p', 'a', 's', 's', 'e', 'd'};
    CharArrayList list(passed, 6);

    /* Should print - "index (6) not in range [0..6)" */
    try
    {
        list.replaceAt('X', 6);
    }
    catch(const std::range_error& e)
    {
        std::cerr << e.what() << '\n';
        return 0;
    }
    
    
    std::cout << "This should not print! Student did not correctly "
                 "throw a range_error."
              << std::endl;
    return 0;
}