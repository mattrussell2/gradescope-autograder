/* 
 * Homework 1 - CS15 - CharArrayList
 *
 * Test 18 - pushAtBack() - 100 element
 *
 * Author: Nickolas Gravel
 *   Date: 9.23.2021
 *
 */ 

#include <iostream>
#include "CharArrayList.h"

int main() {
    char artist[10] = {'A','p','h','e','x','T','w','i','n',' '};

    CharArrayList list;
    
    for (int i = 0; i < 10; i++) {
        for (int j = 0; j < 10; j++) {
            list.pushAtBack(artist[j]);  /* Push to back contents of array */
        }
    }
    std::cout << list.toString() << std::endl;
    return 0;
}
