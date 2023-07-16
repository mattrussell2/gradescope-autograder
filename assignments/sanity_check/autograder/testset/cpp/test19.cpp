#include <cstdlib>
#include <ctime>
#include <iostream>

int main() {
    srand(time(0));
    for (int i = 0; i < 100; i++) {
        std::cerr << rand() << " ";
    }
    return 0;
}