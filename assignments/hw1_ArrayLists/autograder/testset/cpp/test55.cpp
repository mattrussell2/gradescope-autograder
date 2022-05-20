/**
 * CS15 HW1 TEST 55
 * 
 * insertInOrder - Insert 'c' into ['a', 'b', 'd', 'e']
 * 
 * mchamp03
 * 01/25/2022
 */

#include <iostream>
#include "CharArrayList.h"


int main() {
    char inMiddle [] = {'a', 'b', 'd', 'e'};
    CharArrayList list(inMiddle, 4);

    list.insertInOrder('c');

    std::cout << list.toString() << std::endl;
    return 0;
}