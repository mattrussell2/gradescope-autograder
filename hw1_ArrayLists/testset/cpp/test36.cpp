/*
  test36.cpp - concatenate an empty char array list with nonempty one
  Written by: Mateo Hernandez Idrovo
  Sept. 25, 2021
*/

#include <iostream>

#include "CharArrayList.h"

int main() {
    CharArrayList list1;
    char newList[5] = {'h', 'e', 'l', 'l', 'o'};
    CharArrayList list2(newList, 5);

    list1.concatenate(&list2);

    std::cout << list1.toString() << std::endl;

}