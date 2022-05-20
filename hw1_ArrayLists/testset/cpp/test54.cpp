/**
 * CS15 HW1 TEST 54
 * 
 * insertInOrder - Insert 'a' into ['b', 'c', 'd', 'e']
 * 
 * mchamp03
 * 01/25/2022
 */

#include <iostream>
#include "CharArrayList.h"


int main() {
    char infront [] = {'b', 'c', 'd', 'e'};
    CharArrayList list(infront, 4);

    list.insertInOrder('a');

    std::cout << list.toString() << std::endl;
    return 0;
}