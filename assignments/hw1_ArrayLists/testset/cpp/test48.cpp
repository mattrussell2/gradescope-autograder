/**
 * CS15 HW1 TEST 48
 * 
 * size() - while sequentially adding elements
 * 
 * mchamp03
 * 01/25/2022
 */

#include <iostream>
#include "CharArrayList.h"


int main() {

    char numbs[] = {'9', '8', '7', '6', '5', '4', '3', '2', '1', '0'};
    int len      = 10;
    CharArrayList list;

    for (int i = 0; i < len; i++) {
        std::cout << "Size is: " << list.size() << std::endl;
        list.pushAtBack(numbs[i]);
    }
    std::cout << "Size is: " << list.size() << std::endl;

    return 0;
}