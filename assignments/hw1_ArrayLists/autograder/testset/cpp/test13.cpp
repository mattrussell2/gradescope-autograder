/*
 * CS 15 HW1 test13
 * Last()
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
    std::cout << list1.last() << std::endl;

    char comp[3] = {'X', 'Y', 'Z'};
    CharArrayList list2(comp, 3);
    /* Should print - "Z" */
    std::cout << list2.last() << std::endl;
}