/**
 * CS15 HW1 TEST 26
 * 
 * insertAt() index 0
 * 
 * mchamp03
 * 9/25/2021
 */

#include <iostream>
#include "CharArrayList.h"


int main() {

    char passe[]  = {'a', 's', 's', 'e', 'd'};

    CharArrayList passed(passe, 5);
    passed.insertAt('p', 0);

    /* should print [CharArrayList of size 6 <<passed>>] */ 
    std::cout << passed.toString() << std::endl;
    return 0;
}