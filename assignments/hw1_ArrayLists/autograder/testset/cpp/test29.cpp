/**
 * CS15 HW1 TEST 29
 * 
 * popFromBack() - Empty List
 * 
 * mchamp03
 * 9/25/2021
 */

#include <iostream>
#include "CharArrayList.h"


int main() {
    CharArrayList list;
    /* Should print - "cannot pop from empty ArrayList" */
    try
    {
        list.popFromBack();
    }
    catch(const std::runtime_error& e)
    {
        std::cerr << e.what() << '\n';
        return 0;
    }

    // The below should not print
    std::cout << "This should not print! Student did not correctly throw a "
                 "runtime_error." 
              << std::endl;
    return 0;
    
}