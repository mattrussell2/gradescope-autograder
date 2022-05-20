/*
  test35.cpp - concatenate two empty char array lists
  Written by: Mateo Hernandez Idrovo
  Sept. 25, 2021
*/

#include <iostream>

#include "CharArrayList.h"

int main() {
    CharArrayList list1;
    CharArrayList list2;

    list1.concatenate(&list2);

    std::cout << list1.toString() << std::endl;
    std::cout << list2.toString() << std::endl;

}