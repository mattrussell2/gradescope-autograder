/*
 * CS 15 HW1 test15
 * ElementAt()
 * On non-empty ArrayList
 * 
 * Ethan  Harvey
 * 09/24/2021
 */
#include "CharArrayList.h"
#include <iostream>

int main() {
    CharArrayList list1('A');
    /* Should print - "A" */
    std::cout << list1.elementAt(0) << std::endl;

    char comp[3] = {'X', 'Y', 'Z'};
    CharArrayList list2(comp, 3);
    /* Should print - "Y" */
    std::cout << list2.elementAt(1) << std::endl;
}