/*
 * CS 15 HW1 test12
 * Last()
 * On empty ArrayList
 * 
 * Ethan  Harvey
 * 09/24/2021
 */
#include "CharArrayList.h"
#include <iostream>

int main() {
    CharArrayList list1;
    /* Should print - "cannot get last of empty ArrayList" */
    try
    {
        std::cout << list1.last() << std::endl;
    }
    catch(const std::runtime_error& e)
    {
        std::cerr << e.what() << '\n';
        return 0;
    }
    
    // The below should not print
    std::cout << "This should not print! Student did not correctly throw a runtime_error." 
              << std::endl;
    return 0;
}