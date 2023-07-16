#include <fstream>
#include <iostream>

int main(int argc, char **argv) {
    std::string   fnamea = argv[1];
    std::string   fnameb = argv[2];
    std::ofstream ofa(fnamea);
    std::ofstream ofb(fnameb);

    ofa << "Hello" << std::endl;
    ofb << "world!" << std::endl;

    std::cout << "hello cout!" << std::endl;
    std::cerr << "hello cerr!" << std::endl;
    return 0;
}