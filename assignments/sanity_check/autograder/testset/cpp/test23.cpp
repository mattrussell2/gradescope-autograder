
int main(int argc, char **argv) {
    int *x = new int[100];
    int  z;
    for (int i = 0; i < 200; i++) {
        z += x[i];
    }
    delete x;
    return 0;
}