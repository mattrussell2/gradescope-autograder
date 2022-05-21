/*
  test77.cpp - concatenates a non empty char array list with a nonempty one
  Written by: Mateo Hernandez Idrovo
  Sept. 25, 2021
*/

#include <iostream>

#include "CharArrayList.h"

int main() {
    char array1[4] = {'W', 'h', 'a', 't'}; 
    char array2[6] = {' ', 'I', 's', ' ', 'U', 'p'};

    CharArrayList list1(array1, 4);
    CharArrayList list2(array2, 6);

    std::cout << list1.toString() << " + ";
    std::cout << list2.toString() << " == ";

    list1.concatenate(&list2);

    std::cout << list1.toString() << std::endl;
    std::cout << "Making sure contents of other list did not change...\n";
    std::cout << list2.toString() << std::endl;

}