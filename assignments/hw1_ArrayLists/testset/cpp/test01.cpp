/**
 * CS15 HW1 TEST 01
 *
 * Tests Default Constructor ArrayList
 *
 * abui02
 * 9/23/2021
 *
 * mchamp03 - 01/25/2022
 * - made consistent with SP 2022 spec
 */

#include "CharArrayList.h"
#include <iostream>

int main() {
    CharArrayList list1;

    /* should print - [CharArrayList of size 0 <<>>] */
    std::cout << list1.toString() << std::endl;
}