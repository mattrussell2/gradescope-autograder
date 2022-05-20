/**
 * CS15 HW1 TEST 06
 * 
 * Tests Clear - empty ArrayList
 * 
 * abui02
 * 9/23/2021
 */
#include "CharArrayList.h"
#include <iostream>

int main() {
    CharArrayList list1;

    list1.clear();

    /* should print: [CharArrayList of size 0 <<>>] */
    std::cout << list1.toString() << std::endl;

    if (list1.isEmpty()) {
        std::cout << "PASS: Student correctly called clear() on an empty ArrayList." << std::endl;
    } else {
        std::cout << "FAIL: Student incorrectly called clear() on an empty ArrayList." << std::endl;
    }
}