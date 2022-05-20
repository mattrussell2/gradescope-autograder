/*
 * CS 15 HW1 test09
 * Size()
 * On non-empty ArrayList
 * 
 * Ethan  Harvey
 * 09/24/2021
 */
#include "CharArrayList.h"
#include <iostream>

int main() {
    CharArrayList list1('A');
    /* Should print - 1 */
    std::cout << list1.size() << std::endl;

    char comp[3] = {'A', 'B', 'C'};
    CharArrayList list2(comp, 3);
    /* Should print - 3 */
    std::cout << list2.size() << std::endl;
}