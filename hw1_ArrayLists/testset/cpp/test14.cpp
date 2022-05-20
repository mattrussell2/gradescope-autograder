/*
 * CS 15 HW1 test14
 * ElementAt()
 * On empty ArrayList
 * 
 * Ethan  Harvey
 * 09/24/2021
 */
#include "CharArrayList.h"
#include <iostream>

int main() {
    CharArrayList list1;
    /* Should print - "index 6 not in range [0..0)" */
    try
    {
        std::cout << list1.elementAt(6) << std::endl;
    }
    catch(const std::range_error& e)
    {
        std::cerr << e.what() << '\n';
    }
    
    
}