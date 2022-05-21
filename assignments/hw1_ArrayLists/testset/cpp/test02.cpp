/**
 * CS15 HW1 TEST 02
 * 
 * Tests Second Constructor ArrayList
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
    CharArrayList list1('m');

    /* should print - [CharArrayList of size 1 <<m>>] */
    std::cout << list1.toString() << std::endl;
}