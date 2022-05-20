/**
 * CS15 HW1 TEST 46
 * 
 * toReverseString()
 * 
 * mchamp03
 * 01/25/2022
 */

#include <iostream>
#include "CharArrayList.h"


int main() {

    char Alice[] = {'A', 'l', 'i', 'c', 'e'};
    CharArrayList list(Alice, 5);

    /* Should print - "[CharArrayList of size 5 <<ecilA>>]" */
    std::cout << list.toReverseString() << std::endl;


    return 0;
}