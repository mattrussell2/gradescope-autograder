/**
 * CS15 HW1 TEST 03
 * 
 * Tests Third Constructor ArrayList
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
    char comp[7] = {'C', 'o', 'm', 'p', ' ', '1', '5'};

    CharArrayList list1(comp, 7);
    /* should print - [CharArrayList of size 7 <<Comp 15>>] */
    std::cout << list1.toString() << std::endl;

    CharArrayList list2(comp, 4);
    /* should print - [CharArrayList of size 4 <<Comp>>] */
    std::cout << list2.toString() << std::endl;
}
