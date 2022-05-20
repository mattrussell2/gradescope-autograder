/**
 * CS15 HW1 TEST 04
 * 
 * Tests IsEmpty - empty ArrayList
 * 
 * abui02
 * 9/23/2021\ 
 * 
 * mchamp03 - 01/25/2022
 * - made consistent with SP 2022 spec
 */
#include "CharArrayList.h"
#include <iostream>

int main() {
    CharArrayList list1;

    if (list1.isEmpty()) {
        std::cout << "PASS: Student correctly returned True from isEmpty()" << std::endl;
    } else {
        std::cout << "FAIL: Student incorrectly returned False from isEmpty()" << std::endl;
    }
}