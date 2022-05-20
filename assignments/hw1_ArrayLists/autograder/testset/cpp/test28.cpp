/**
 * CS15 HW1 TEST 27
 * 
 * popFromFront() - Non-Empty List
 * 
 * mchamp03
 * 9/25/2021
 */

#include <iostream>
#include "CharArrayList.h"


int main() {
    char passed[] = {'X', 'p', 'o', 'p', '_', 'm', 'e'};
    CharArrayList list(passed, 7);
    list.popFromFront();

    /* Should print - [CharArrayList of size 6 <<pop_me>>] */
    std::cout << list.toString() << std::endl;

    // Make sure subsequent pops doesn't crash
    for (int i = 0; i < 6; i++) {
        list.popFromFront();
    }
    /* Should print - [CharArrayList of size 0 <<>>] */
    std::cout << list.toString() << std::endl;
    return 0;
}