/**
 * CS15 HW1 TEST 44
 * 
 * removeAt - Out of Bounds - index[-1]
 * 
 * mchamp03
 * 9/25/2021
 */

#include <iostream>
#include "CharArrayList.h"


int main() {

    char passed[] = {'p', 'a', 's', 's', 'e', 'd'};
    CharArrayList list(passed, 6);

    try
    {
        list.removeAt(-1);
    }
    catch(const std::range_error& e)
    {
        std::cerr << e.what() << '\n';
        return 0;
    }
    
    
    /*should print - "index (-1) not in range [0..6)" */
    std::cout << "This should not print! Student did not correctly "
                 "throw a range_error."
              << std::endl;
    
    return 0;
}