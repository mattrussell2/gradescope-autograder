/**
 * CS15 HW1 TEST 57
 * 
 * insertInOrder - Stress Test
 * 
 * mchamp03
 * 01/25/2022
 */

#include <iostream>
#include "CharArrayList.h"


int main() {
    char randStr [] = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 
                       'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
                       'w', 'x', 'y', 'z'};
    CharArrayList list(randStr, 26);

    std::cout << "Original String: " << list.toString() << std::endl;

    // insert [a-z] into the list.
    for (int i = 0; i < 26; i++) {
        list.insertInOrder(i + 97);
    }
    
    std::cout << "insertInOrder [a-z] ... " << std::endl;
    std::cout << list.toString() << std::endl;
    return 0;
}