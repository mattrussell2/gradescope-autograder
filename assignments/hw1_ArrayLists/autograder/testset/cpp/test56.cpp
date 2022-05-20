/**
 * CS15 HW1 TEST 56
 * 
 * insertInOrder - Insert 'z' into ['a', 'b', 'c', 'd']
 * 
 * mchamp03
 * 01/25/2022
 */

#include <iostream>
#include "CharArrayList.h"


int main() {
    char abcd [] = {'a', 'b', 'c', 'd'};
    CharArrayList list(abcd, 4);

    list.insertInOrder('z');

    std::cout << list.toString() << std::endl;
    return 0;
}