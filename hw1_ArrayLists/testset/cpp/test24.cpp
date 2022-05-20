/**
 * CS15 HW1 TEST 24
 * 
 * insertAt() at size-th position in array
 * 
 * mchamp03
 * 9/25/2021
 */

#include <iostream>
#include "CharArrayList.h"


int main() {

    char passe[]  = {'p', 'a', 's', 's', 'e'};

    CharArrayList passed(passe, 5);
    passed.insertAt('d', 5);

    /* should print [CharArrayList of size 6 <<passed>>] */ 
    std::cout << passed.toString() << std::endl;

    return 0;
}