/**
 * CS15 HW1 TEST 53
 * 
 * insertInOrder - Empty List
 * 
 * mchamp03
 * 01/25/2022
 */

#include <iostream>
#include "CharArrayList.h"


int main() {

    CharArrayList list;

    list.insertInOrder('A');

    std::cout << list.toString() << std::endl;
    return 0;
}