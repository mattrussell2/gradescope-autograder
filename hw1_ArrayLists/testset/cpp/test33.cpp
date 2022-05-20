/**
 * CS15 HW1 TEST 33
 * 
 * replace - in range
 * 
 * mchamp03
 * 9/25/2021
 */

#include <iostream>
#include "CharArrayList.h"


int main() {
    char to_fill[] = {'_', '_', 'X', 'X', 'X', 'X', 'X', 'X', '_', '_'};
    char passed[]  = {'p', 'a', 's', 's', 'e', 'd'};
    CharArrayList list(to_fill, 10);

    // Make sure subsequent pops doesn't crash
    for (int i = 2; i < 8; i++) {
        list.replaceAt(passed[i - 2], i);
    }
    /* Should print - [CharArrayList of size 10 <<__passed__>>]*/
    std::cout << list.toString() << std::endl;
    return 0;
}