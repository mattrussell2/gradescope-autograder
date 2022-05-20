/**
 * CS15 HW1 TEST 23
 * 
 * insertAt() in bounds
 * 
 * mchamp03
 * 9/25/2021
 */

#include <iostream>
#include "CharArrayList.h"


int main() {
    char missing_i[]  = {'m', 's', 's', 'i', 'n', 'g'};

    CharArrayList list(missing_i, 6);
    list.insertAt('i', 1);
    /* should print [CharArrayList of size 7 <<missing>>]*/
    std::cout << list.toString() << std::endl;

    // Do 10 inserts within range
    for (int i = 3; i < 13; i++) {
        if (i == 3 or i == 12) {
            list.insertAt('_', i);
        } else {
            list.insertAt((i % 26) + 93, i); // adds 'a' -> 'h'
        }
        
    }
    /*should print [CharArrayList of size 17 <<mis_abcdefgh_sing>>] */
    std::cout << list.toString() << std::endl;
    
    return 0;
}