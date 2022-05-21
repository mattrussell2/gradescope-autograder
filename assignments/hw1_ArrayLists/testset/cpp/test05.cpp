/**
 * CS15 HW1 TEST 05
 * 
 * Tests IsEmpty - non-empty ArrayList
 * 
 * abui02
 * 9/23/2021
 */
#include "CharArrayList.h"
#include <iostream>

int main() {
    CharArrayList list1('p');

    if (list1.isEmpty()) {
        std::cout << "FAIL: Student incorrectly returned True from isEmpty()" << std::endl;
    } else {
        std::cout << "PASS: Student correctly returned False from isEmpty()" << std::endl;
    }
}