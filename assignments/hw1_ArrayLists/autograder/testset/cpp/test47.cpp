/**
 * CS15 HW1 TEST 47
 * 
 * size() - while sequentially removing elements
 * 
 * mchamp03
 * 9/25/2021
 */

#include <iostream>
#include "CharArrayList.h"


int main() {

    char numbs[] = {'9', '8', '7', '6', '5', '4', '3', '2', '1', '0'};
    CharArrayList list(numbs, 10);

    while (! list.isEmpty()) {
        list.popFromFront();
        std::cout << "Size is: " << list.size() << std::endl;
    }


    return 0;
}