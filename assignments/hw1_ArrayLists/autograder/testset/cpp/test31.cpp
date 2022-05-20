/**
 * CS15 HW1 TEST 31
 * 
 * removeAt() - in-range
 * 
 * mchamp03
 * 9/25/2021
 */

#include <iostream>
#include "CharArrayList.h"


int main() {
    char passed[] = {'p', 'a', 'X', 's', 'X', 's', 'X', 'e', 'X', 'd'};
    CharArrayList list(passed, 10);

    // remove all 'X's
    for (int i = 2; i < 6; i++) {
        list.removeAt(i);
    }
    /* Should print - [CharArrayList of size 6 <<passed>>]*/
    std::cout << list.toString() << std::endl;
    return 0;
}