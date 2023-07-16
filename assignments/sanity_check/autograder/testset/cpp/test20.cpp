#include <cstdlib>
#include <ctime>
#include <fstream>
#include <iostream>

int main(int argc, char **argv) {
    std::string   fname = argv[1];
    std::ofstream of(fname);

    srand(time(0));
    for (int i = 0; i < 100; i++) {
        of << rand() << " ";
    }
    return 0;
}