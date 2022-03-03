#include <stdlib.h>
#include <stdio.h>

#define SIZE 1000
int
main(int argc, char *argv[])
{
	char buffer[SIZE];

	printf("Buffer of size %u on stack at address %p will be freed!\n",
	       SIZE, buffer);
	
	exit(EXIT_SUCCESS);
}
