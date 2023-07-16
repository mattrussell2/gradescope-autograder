#include <iostream>

int main() {
    int *x = new int[100];
    delete[] x;
    return 0;
}